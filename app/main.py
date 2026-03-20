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
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from app.agents import ResearcherAgent
from app.agents.base import DEFAULT_MODEL, FREE_MODELS, MODEL_TIERS, PREMIUM_MODEL
from app.models import (
    Currency,
    DealInput,
    PricingResult,
    StructuredInsights,
)
from app.auth import AuthMiddleware, SESSION_COOKIE, create_session_token
from app.swarm import run_swarm_streaming
import app.db as db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("precio")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Precio - B2B Pricing Swarm")
app.add_middleware(AuthMiddleware)
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

_premium_short = PREMIUM_MODEL.split("/")[-1][:30]
_free_short = DEFAULT_MODEL.split("/")[-1][:30]

_MODEL_TIER_OPTIONS = [
    {"id": "free", "label": f"Free ({_free_short})"},
    {"id": "premium", "label": f"Premium ({_premium_short}) - Arbiter + Negotiation"},
]

_current_model_tier = "premium"


def _uid(request: Request) -> str:
    """Get the authenticated user ID from request."""
    return getattr(request.state, "user_id", "")


def save_result_to_db(user_id: str, deal: DealInput, result) -> str:
    """Persist a pricing result to SQLite."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    domain = deal.business_url.replace("https://", "").replace("http://", "").split("/")[0]
    filename = f"{ts}_{domain}.json"
    deal_json = json.dumps(deal.model_dump(mode="json"), default=str)
    result_json = json.dumps(result.model_dump(mode="json"), default=str)
    db.save_result(user_id, deal.business_id, filename, deal_json, result_json)
    logger.info("Result saved: %s for user %s", filename, user_id)
    return filename


# === Auth Routes ===

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.authenticate(email, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password."})
    token = create_session_token(user["id"])
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, max_age=60*60*24*30, httponly=True, samesite="lax")
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None, "free_credits": db.FREE_CREDITS})


@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, email: str = Form(...), password: str = Form(...)):
    if len(password) < 8:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Password must be at least 8 characters.", "free_credits": db.FREE_CREDITS})
    user = db.create_user(email, password)
    if not user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "An account with that email already exists.", "free_credits": db.FREE_CREDITS})
    token = create_session_token(user["id"])
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, max_age=60*60*24*30, httponly=True, samesite="lax")
    return response


@app.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user = db.get_user(_uid(request))
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})


@app.post("/settings/key")
async def settings_key(request: Request, api_key: str = Form("")):
    db.update_user_key(_uid(request), api_key.strip())
    return RedirectResponse(url="/settings", status_code=303)



def _form_ctx(request, prefill=None):
    """Common context for the pricing form."""
    uid = _uid(request)
    user = db.get_user(uid)
    return {
        "request": request,
        "currencies": [c.value for c in Currency],
        "prefill": prefill or {},
        "model_tiers": _MODEL_TIER_OPTIONS,
        "current_model": _current_model_tier,
        "businesses": db.list_businesses(uid),
        "services": db.list_services(uid),
        "user": user,
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

    # Check credits
    uid = _uid(request)
    if not uid:
        return RedirectResponse(url="/login", status_code=302)
    user = db.get_user(uid)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not db.use_credit(uid):
        if user["credits_remaining"] <= 0 and not user["openrouter_key"]:
            return RedirectResponse(url="/settings", status_code=303)
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Daily run limit reached (20/day). Try again tomorrow.", "deal": deal},
        )

    # Set API key for this run (user's own key or server default)
    import app.agents.base as base_mod2
    api_key = db.get_user_api_key(uid)
    if api_key:
        base_mod2._client = None  # reset client to pick up new key
        os.environ["OPENROUTER_API_KEY"] = api_key

    # Create a job and return the progress page immediately
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"deal": deal, "status": "starting", "result": None, "error": None, "user_id": uid}

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

        # Step 3: Persist to database
        user_id = job.get("user_id", "")
        result_filename = save_result_to_db(user_id, deal, result)

        job["result"] = result
        job["result_filename"] = result_filename
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
async def history(request: Request, q: str = "", currency: str = ""):
    results = db.list_results(_uid(request), search=q, currency=currency)
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "results": results, "search_q": q, "search_currency": currency,
         "currencies": [c.value for c in Currency]},
    )


@app.get("/history/{filename}", response_class=HTMLResponse)
async def history_detail(request: Request, filename: str):
    row = db.get_result(_uid(request), filename)
    if not row:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Result not found.", "deal": DealInput(service_description="", business_url="")},
        )
    deal = DealInput(**json.loads(row["deal_json"]))
    result = PricingResult(**json.loads(row["result_json"]))
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "deal": deal, "result": result,
         "result_filename": filename, "result_note": row.get("note", "")},
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
        pass  # RedirectResponse already imported at top
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
        {"request": request, "businesses": db.list_businesses(_uid(request))},
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
    pass  # RedirectResponse already imported at top
    biz = db.save_business(_uid(request), None, name, url, industry, notes)
    return RedirectResponse(url=f"/businesses/{biz['id']}", status_code=303)


@app.get("/businesses/{biz_id}", response_class=HTMLResponse)
async def business_detail(request: Request, biz_id: str):
    uid = _uid(request)
    biz = db.get_business(uid, biz_id)
    if not biz:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Business not found.", "deal": DealInput(service_description="", business_url="")},
        )
    runs = db.get_business_results(uid, biz_id)
    return templates.TemplateResponse(
        "business_detail.html",
        {"request": request, "biz": biz, "runs": runs, "services": db.list_services(uid)},
    )


@app.get("/businesses/{biz_id}/price", response_class=HTMLResponse)
async def business_price(request: Request, biz_id: str, svc: str = ""):
    uid = _uid(request)
    biz = db.get_business(uid, biz_id)
    if not biz:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Business not found.", "deal": DealInput(service_description="", business_url="")},
        )
    prefill = {"business_url": biz["url"], "business_id": biz_id}
    svc_obj = db.get_service(uid, svc) if svc else None
    if svc_obj:
        prefill["service_description"] = svc_obj["description"]
        prefill["constraints"] = svc_obj.get("default_constraints", "")
        prefill["service_template_id"] = svc_obj["id"]
        prefill["our_hours_estimate"] = str(svc_obj.get("estimated_hours") or "")
        prefill["our_hourly_rate"] = str(svc_obj.get("hourly_rate") or "")
        prefill["normal_delivery_days"] = str(svc_obj.get("normal_delivery_days") or "")
        prefill["fast_delivery_days"] = str(svc_obj.get("fast_delivery_days") or "")
    return templates.TemplateResponse("index.html", _form_ctx(request, prefill))


# === Service Templates ===

@app.get("/services", response_class=HTMLResponse)
async def services_list(request: Request):
    return templates.TemplateResponse(
        "services.html",
        {"request": request, "services": db.list_services(_uid(request))},
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
    pass  # RedirectResponse already imported at top
    db.save_service(_uid(request), None,
        name=name, description=description, default_constraints=default_constraints,
        estimated_hours=estimated_hours, hourly_rate=hourly_rate,
        normal_delivery_days=normal_delivery_days, fast_delivery_days=fast_delivery_days)
    return RedirectResponse(url="/services", status_code=303)


@app.get("/services/{svc_id}/edit", response_class=HTMLResponse)
async def service_edit(request: Request, svc_id: str):
    svc = db.get_service(_uid(request), svc_id)
    if not svc:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Service not found.", "deal": DealInput(service_description="", business_url="")})
    return templates.TemplateResponse("service_form.html", {"request": request, "svc": svc})


@app.post("/services/{svc_id}/edit")
async def service_update(
    request: Request, svc_id: str,
    name: str = Form(...), description: str = Form(...),
    default_constraints: str = Form(""),
    estimated_hours: float | None = Form(None), hourly_rate: float | None = Form(None),
    normal_delivery_days: int | None = Form(None), fast_delivery_days: int | None = Form(None),
):
    pass  # RedirectResponse already imported at top
    db.save_service(_uid(request), svc_id,
        name=name, description=description, default_constraints=default_constraints,
        estimated_hours=estimated_hours, hourly_rate=hourly_rate,
        normal_delivery_days=normal_delivery_days, fast_delivery_days=fast_delivery_days)
    return RedirectResponse(url="/services", status_code=303)


@app.post("/services/{svc_id}/delete")
async def service_delete(request: Request, svc_id: str):
    db.delete_service(_uid(request), svc_id)
    return RedirectResponse(url="/services", status_code=303)


# === Business Edit/Delete ===

@app.get("/businesses/{biz_id}/edit", response_class=HTMLResponse)
async def business_edit(request: Request, biz_id: str):
    biz = db.get_business(_uid(request), biz_id)
    if not biz:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Business not found.", "deal": DealInput(service_description="", business_url="")})
    return templates.TemplateResponse("business_form.html", {"request": request, "biz": biz})


@app.post("/businesses/{biz_id}/edit")
async def business_update(
    request: Request, biz_id: str,
    name: str = Form(...), url: str = Form(...),
    industry: str = Form(""), notes: str = Form(""),
):
    pass  # RedirectResponse already imported at top
    db.save_business(_uid(request), biz_id, name, url, industry, notes)
    return RedirectResponse(url=f"/businesses/{biz_id}", status_code=303)


@app.post("/businesses/{biz_id}/delete")
async def business_delete(request: Request, biz_id: str):
    db.delete_business(_uid(request), biz_id)
    return RedirectResponse(url="/businesses", status_code=303)


# === Notes on Pricing Results ===

@app.post("/history/{filename}/note")
async def add_note(request: Request, filename: str, note: str = Form("")):
    db.add_note_to_result(_uid(request), filename, note)
    return RedirectResponse(url=f"/history/{filename}", status_code=303)


# === Service API for JS auto-populate ===

@app.get("/api/services/{svc_id}")
async def api_service(request: Request, svc_id: str):
    svc = db.get_service(_uid(request), svc_id)
    if not svc:
        return {"error": "not found"}
    return svc


# === Dashboard ===

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = db.dashboard_stats(_uid(request))
    user = db.get_user(_uid(request))
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, **stats},
    )
