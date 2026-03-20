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
    Currency,
    DealInput,
    PricingResult,
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



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "currencies": [c.value for c in Currency], "prefill": {},
         "model_tiers": _MODEL_TIER_OPTIONS, "current_model": _current_model_tier},
    )


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
    """Pre-fill the form with values from a previous run."""
    prefill = {
        "business_url": url,
        "service_description": service,
        "constraints": constraints,
        "budget_hint": budget,
        "currency": currency,
        "insights": insights,
    }
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "currencies": [c.value for c in Currency], "prefill": prefill,
         "model_tiers": _MODEL_TIER_OPTIONS, "current_model": _current_model_tier},
    )


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
    model_tier: str = Form("free"),
):
    # Apply model selection for this run
    # "premium" = use premium for Arbiter+Negotiation, free for rest (default)
    # "free" = use free models for everything
    import app.agents.base as base_mod
    import app.agents.arbiter as arbiter_mod
    if model_tier == "free":
        arbiter_mod.ArbiterAgent.model = base_mod.DEFAULT_MODEL
    else:
        arbiter_mod.ArbiterAgent.model = base_mod.PREMIUM_MODEL

    deal = DealInput(
        service_description=service_description,
        business_url=business_url,
        constraints=constraints,
        budget_hint=budget_hint if budget_hint else None,
        currency=Currency(currency),
        insights=insights,
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
        # Step 1: Research
        job["status"] = "researching"
        researcher = ResearcherAgent()
        client_context = await researcher.research(deal.business_url)
        deal = deal.model_copy(update={"client_context": client_context})
        job["deal"] = deal

        # Step 2: Run swarm with status callbacks
        async def on_status(status: str):
            job["status"] = status

        result = await run_swarm_streaming(deal, on_status)

        # Step 3: Persist
        result_path = save_result(deal, result)

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
