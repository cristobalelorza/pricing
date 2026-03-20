from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from app.agents import ResearcherAgent
from app.agents.base import DEFAULT_MODEL, FREE_MODELS, MODEL_TIERS, PREMIUM_MODEL
from app.models import (
    Business,
    Currency,
    DealInput,
    PricingResult,
    ServiceTemplate,
    StructuredInsights,
)
from app.storage import (
    add_pricing_run_to_business,
    get_business,
    get_service,
    list_businesses,
    list_services,
    new_id,
    save_business,
    save_service,
)
from app.swarm import run_swarm_streaming

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("precio")

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Precio - B2B Pricing Swarm")
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

_premium_short = PREMIUM_MODEL.split("/")[-1][:30]
_free_short = DEFAULT_MODEL.split("/")[-1][:30]

_MODEL_TIER_OPTIONS = [
    {"id": "free", "label": f"Free ({_free_short})"},
    {"id": "premium", "label": f"Premium ({_premium_short}) - Arbiter + Negotiation"},
]

_current_model_tier = "premium"  # default: use premium for critical agents


def save_result(deal: DealInput, result) -> Path:
    """Persist a pricing result to disk as JSON."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    domain = deal.business_url.replace("https://", "").replace("http://", "").split("/")[0]
    filename = f"{ts}_{domain}.json"
    path = RESULTS_DIR / filename

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "deal": deal.model_dump(mode="json"),
        "result": result.model_dump(mode="json"),
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    logger.info("Result saved to %s", path)
    return path



def _form_ctx(request, prefill=None):
    """Common context for the pricing form."""
    return {
        "request": request,
        "currencies": [c.value for c in Currency],
        "prefill": prefill or {},
        "model_tiers": _MODEL_TIER_OPTIONS,
        "current_model": _current_model_tier,
        "businesses": list_businesses(),
        "services": list_services(),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", _form_ctx(request))


@app.get("/rerun", response_class=HTMLResponse)
async def rerun(
    request: Request,
    url: str = "",
    service: str = "",
    constraints: str = "",
    budget: str = "",
    currency: str = "USD",
    insights: str = "",
):
    prefill = {
        "business_url": url,
        "service_description": service,
        "constraints": constraints,
        "budget_hint": budget,
        "currency": currency,
        "insights": insights,
    }
    return templates.TemplateResponse("index.html", _form_ctx(request, prefill))


# In-memory store for pending pricing jobs
_jobs: dict[str, dict] = {}


@app.post("/price", response_class=HTMLResponse)
async def price(
    request: Request,
    service_description: str = Form(...),
    business_url: str = Form(...),
    constraints: str = Form(""),
    budget_hint: float | None = Form(None),
    currency: str = Form("USD"),
    insights: str = Form(""),
    model_tier: str = Form("premium"),
    business_id: str = Form(""),
    service_template_id: str = Form(""),
    # Structured insights fields
    has_competitor: str = Form(""),
    competitor_url: str = Form(""),
    competitor_monthly_price: float | None = Form(None),
    competitor_likes: str = Form(""),
    competitor_dislikes: str = Form(""),
    our_hours_estimate: float | None = Form(None),
    our_hourly_rate: float | None = Form(None),
    delivery_speed: str = Form("normal"),
    normal_delivery_days: int | None = Form(None),
    fast_delivery_days: int | None = Form(None),
    wtp_signals: str = Form(""),
    owner_priorities: list[str] = Form([]),
    deal_breakers: str = Form(""),
    additional_notes: str = Form(""),
):
    # Apply model selection
    import app.agents.base as base_mod
    import app.agents.arbiter as arbiter_mod
    if model_tier == "free":
        arbiter_mod.ArbiterAgent.model = base_mod.DEFAULT_MODEL
    else:
        arbiter_mod.ArbiterAgent.model = base_mod.PREMIUM_MODEL

    # Build structured insights
    si = StructuredInsights(
        has_competitor=has_competitor == "on",
        competitor_url=competitor_url,
        competitor_monthly_price=competitor_monthly_price,
        competitor_likes=competitor_likes,
        competitor_dislikes=competitor_dislikes,
        our_hours_estimate=our_hours_estimate,
        our_hourly_rate=our_hourly_rate,
        delivery_speed=delivery_speed,
        normal_delivery_days=normal_delivery_days,
        fast_delivery_days=fast_delivery_days,
        wtp_signals=wtp_signals,
        owner_priorities=[p for p in owner_priorities if p],
        deal_breakers=deal_breakers,
        additional_notes=additional_notes,
    )

    deal = DealInput(
        service_description=service_description,
        business_url=business_url,
        constraints=constraints,
        budget_hint=budget_hint if budget_hint else None,
        currency=Currency(currency),
        insights=insights,
        structured_insights=si,
        business_id=business_id,
        service_template_id=service_template_id,
    )

    # Create a job and return the progress page immediately
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"deal": deal, "status": "starting", "result": None, "error": None}

    # Start the swarm in the background
    asyncio.create_task(_run_job(job_id))

    return templates.TemplateResponse(
        "progress.html",
        {"request": request, "deal": deal, "job_id": job_id},
    )


async def _run_job(job_id: str):
    """Run the pricing swarm in the background, updating job status."""
    job = _jobs[job_id]
    deal = job["deal"]

    try:
        # Step 1: Research client
        job["status"] = "researching"
        researcher = ResearcherAgent()
        client_context = await researcher.research(deal.business_url)
        deal = deal.model_copy(update={"client_context": client_context})

        # Step 1b: Scrape competitor if provided
        si = deal.structured_insights
        if si and si.has_competitor and si.competitor_url and not si.competitor_features:
            from app.agents.researcher import _scrape_url
            from app.agents.base import get_client, FREE_MODELS
            scraped = _scrape_url(si.competitor_url)
            if scraped:
                client = get_client()
                try:
                    resp = await client.chat.completions.create(
                        model=FREE_MODELS[0] if FREE_MODELS else "arcee-ai/trinity-large-preview:free",
                        max_tokens=1024,
                        messages=[
                            {"role": "system", "content": "Compare the features of a competitor service with our service. List what the competitor offers, what we offer that they don't, and key differences. Be concise."},
                            {"role": "user", "content": f"## Our service\n{deal.service_description}\n\n## Competitor website content\n{scraped[:3000]}"},
                        ],
                    )
                    comp_text = resp.choices[0].message.content
                    if comp_text:
                        si = si.model_copy(update={"competitor_features": comp_text.strip()})
                        deal = deal.model_copy(update={"structured_insights": si})
                except Exception as e:
                    logger.warning("Competitor scrape LLM failed: %s", e)

        job["deal"] = deal

        # Step 2: Run swarm with status callbacks
        async def on_status(status: str):
            job["status"] = status

        result = await run_swarm_streaming(deal, on_status)

        # Step 3: Persist and link to business
        result_path = save_result(deal, result)
        if deal.business_id:
            add_pricing_run_to_business(deal.business_id, result_path.name)

        job["result"] = result
        job["result_filename"] = result_path.name
        job["status"] = "done"
    except Exception as e:
        logger.exception("Swarm failed for job %s", job_id)
        job["error"] = str(e)
        job["status"] = "error"


@app.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    """SSE endpoint streaming agent progress updates."""
    async def event_generator():
        last_status = None
        while True:
            job = _jobs.get(job_id)
            if not job:
                yield {"event": "error", "data": "Job not found"}
                return

            if job["status"] != last_status:
                last_status = job["status"]
                yield {"event": "status", "data": last_status}

            if job["status"] == "done":
                result = job["result"]
                data = json.dumps({
                    "floor": result.price_floor,
                    "target": result.price_target,
                    "stretch": result.price_stretch,
                    "currency": result.currency.value,
                    "structure": result.suggested_structure,
                    "confidence": result.confidence,
                    "valid": result.validation.is_valid if result.validation else None,
                })
                yield {"event": "result", "data": data}
                return

            if job["status"] == "error":
                yield {"event": "error", "data": job["error"]}
                del _jobs[job_id]
                return

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/result/{job_id}", response_class=HTMLResponse)
async def result_page(request: Request, job_id: str):
    """Render the final result page after job completes."""
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Job not found or still running. Check /history for past results.", "deal": DealInput(service_description="", business_url="")},
        )
    result = job["result"]
    deal = job["deal"]
    result_filename = job.get("result_filename", "")
    _jobs.pop(job_id, None)
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "deal": deal, "result": result, "result_filename": result_filename},
    )


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Show saved pricing results."""
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            results.append({
                "filename": path.name,
                "timestamp": data["timestamp"],
                "url": data["deal"]["business_url"],
                "service": data["deal"]["service_description"][:80],
                "floor": data["result"]["price_floor"],
                "target": data["result"]["price_target"],
                "stretch": data["result"]["price_stretch"],
                "currency": data["result"]["currency"],
                "valid": data["result"].get("validation", {}).get("is_valid", None),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "results": results},
    )


@app.get("/history/{filename}", response_class=HTMLResponse)
async def history_detail(request: Request, filename: str):
    """View a saved pricing result."""
    path = RESULTS_DIR / filename
    if not path.exists() or not path.suffix == ".json":
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Result not found.", "deal": DealInput(service_description="", business_url="")},
        )
    data = json.loads(path.read_text())
    deal = DealInput(**data["deal"])
    result = PricingResult(**data["result"])
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "deal": deal, "result": result, "result_filename": filename},
    )


@app.get("/export/{filename}")
async def export_pdf(request: Request, filename: str):
    """Export a saved pricing result as PDF."""
    path = RESULTS_DIR / filename
    if not path.exists() or not path.suffix == ".json":
        return Response("Result not found", status_code=404)

    data = json.loads(path.read_text())
    deal = DealInput(**data["deal"])
    result = PricingResult(**data["result"])

    html_content = templates.get_template("report.html").render(
        deal=deal,
        result=result,
        timestamp=data.get("timestamp", ""),
    )

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()

    pdf_name = filename.replace(".json", ".pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
    )


@app.get("/compare", response_class=HTMLResponse)
async def compare(request: Request, a: str = "", b: str = ""):
    """Compare two pricing results side by side."""
    all_results = []
    for path in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            all_results.append({
                "filename": path.name,
                "label": f"{data['deal']['business_url']} - {data['deal']['service_description'][:50]}",
            })
        except (json.JSONDecodeError, KeyError):
            continue

    result_a = result_b = deal_a = deal_b = None
    if a and b:
        for fn, var in [(a, "a"), (b, "b")]:
            path = RESULTS_DIR / fn
            if path.exists():
                data = json.loads(path.read_text())
                if var == "a":
                    deal_a = DealInput(**data["deal"])
                    result_a = PricingResult(**data["result"])
                else:
                    deal_b = DealInput(**data["deal"])
                    result_b = PricingResult(**data["result"])

    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "all_results": all_results,
            "selected_a": a,
            "selected_b": b,
            "deal_a": deal_a,
            "deal_b": deal_b,
            "result_a": result_a,
            "result_b": result_b,
        },
    )


@app.get("/ab-test", response_class=HTMLResponse)
async def ab_test_form(request: Request):
    """A/B test form: run the same deal with premium vs free models."""
    return templates.TemplateResponse(
        "ab_test.html",
        {"request": request, "currencies": [c.value for c in Currency],
         "model_tiers": _MODEL_TIER_OPTIONS, "status": None},
    )


@app.post("/ab-test", response_class=HTMLResponse)
async def ab_test_run(
    request: Request,
    service_description: str = Form(...),
    business_url: str = Form(...),
    constraints: str = Form(""),
    budget_hint: float | None = Form(None),
    currency: str = Form("USD"),
    insights: str = Form(""),
):
    """Run the same deal with premium and free models, then redirect to compare."""
    import app.agents.base as base_mod
    import app.agents.arbiter as arbiter_mod

    # Research once (shared)
    researcher = ResearcherAgent()
    client_context = await researcher.research(business_url)

    deal = DealInput(
        service_description=service_description,
        business_url=business_url,
        client_context=client_context,
        constraints=constraints,
        budget_hint=budget_hint if budget_hint else None,
        currency=Currency(currency),
        insights=insights,
    )

    results_files = []

    for label, use_premium in [("premium", True), ("free", False)]:
        # Set model for this run
        if use_premium:
            arbiter_mod.ArbiterAgent.model = base_mod.PREMIUM_MODEL
        else:
            arbiter_mod.ArbiterAgent.model = base_mod.DEFAULT_MODEL

        try:
            result = await run_swarm_streaming(deal)
            path = save_result(deal, result)
            results_files.append(path.name)
        except Exception as e:
            logger.exception("A/B test %s run failed", label)
            results_files.append(None)

    # Restore default
    arbiter_mod.ArbiterAgent.model = base_mod.PREMIUM_MODEL

    if results_files[0] and results_files[1]:
        from starlette.responses import RedirectResponse
        return RedirectResponse(
            url=f"/compare?a={results_files[0]}&b={results_files[1]}",
            status_code=303,
        )

    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "One or both A/B test runs failed.", "deal": deal},
    )


# === Business Management ===

@app.get("/businesses", response_class=HTMLResponse)
async def businesses_list(request: Request):
    return templates.TemplateResponse(
        "businesses.html",
        {"request": request, "businesses": list_businesses()},
    )


@app.get("/businesses/new", response_class=HTMLResponse)
async def business_new(request: Request):
    return templates.TemplateResponse(
        "business_form.html",
        {"request": request, "biz": None},
    )


@app.post("/businesses", response_class=HTMLResponse)
async def business_create(
    request: Request,
    name: str = Form(...),
    url: str = Form(...),
    industry: str = Form(""),
    notes: str = Form(""),
):
    from starlette.responses import RedirectResponse
    biz = Business(id=new_id(), name=name, url=url, industry=industry, notes=notes)
    save_business(biz)
    return RedirectResponse(url=f"/businesses/{biz.id}", status_code=303)


@app.get("/businesses/{biz_id}", response_class=HTMLResponse)
async def business_detail(request: Request, biz_id: str):
    biz = get_business(biz_id)
    if not biz:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Business not found.", "deal": DealInput(service_description="", business_url="")},
        )
    from app.storage import get_business_results
    runs = get_business_results(biz_id)
    return templates.TemplateResponse(
        "business_detail.html",
        {"request": request, "biz": biz, "runs": runs, "services": list_services()},
    )


@app.get("/businesses/{biz_id}/price", response_class=HTMLResponse)
async def business_price(request: Request, biz_id: str, svc: str = ""):
    biz = get_business(biz_id)
    if not biz:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Business not found.", "deal": DealInput(service_description="", business_url="")},
        )
    prefill = {"business_url": biz.url, "business_id": biz_id}
    svc_obj = get_service(svc) if svc else None
    if svc_obj:
        prefill["service_description"] = svc_obj.description
        prefill["constraints"] = svc_obj.default_constraints
        prefill["service_template_id"] = svc_obj.id
        prefill["our_hours_estimate"] = str(svc_obj.estimated_hours or "")
        prefill["our_hourly_rate"] = str(svc_obj.hourly_rate or "")
        prefill["normal_delivery_days"] = str(svc_obj.normal_delivery_days or "")
        prefill["fast_delivery_days"] = str(svc_obj.fast_delivery_days or "")
    return templates.TemplateResponse("index.html", _form_ctx(request, prefill))


# === Service Templates ===

@app.get("/services", response_class=HTMLResponse)
async def services_list(request: Request):
    return templates.TemplateResponse(
        "services.html",
        {"request": request, "services": list_services()},
    )


@app.get("/services/new", response_class=HTMLResponse)
async def service_new(request: Request):
    return templates.TemplateResponse(
        "service_form.html",
        {"request": request, "svc": None},
    )


@app.post("/services", response_class=HTMLResponse)
async def service_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    default_constraints: str = Form(""),
    estimated_hours: float | None = Form(None),
    hourly_rate: float | None = Form(None),
    normal_delivery_days: int | None = Form(None),
    fast_delivery_days: int | None = Form(None),
):
    from starlette.responses import RedirectResponse
    svc = ServiceTemplate(
        id=new_id(),
        name=name,
        description=description,
        default_constraints=default_constraints,
        estimated_hours=estimated_hours,
        hourly_rate=hourly_rate,
        normal_delivery_days=normal_delivery_days,
        fast_delivery_days=fast_delivery_days,
    )
    save_service(svc)
    return RedirectResponse(url="/services", status_code=303)
