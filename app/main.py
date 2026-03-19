from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.agents import ResearcherAgent
from app.models import Currency, DealInput
from app.swarm import run_swarm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("precio")

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Precio - B2B Pricing Swarm")
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "currencies": [c.value for c in Currency]},
    )


@app.post("/price", response_class=HTMLResponse)
async def price(
    request: Request,
    service_description: str = Form(...),
    business_url: str = Form(...),
    constraints: str = Form(""),
    budget_hint: float | None = Form(None),
    currency: str = Form("USD"),
):
    # Step 1: Research the client business from their URL
    researcher = ResearcherAgent()
    client_context = await researcher.research(business_url)

    # Step 2: Build deal with auto-populated client context
    deal = DealInput(
        service_description=service_description,
        business_url=business_url,
        client_context=client_context,
        constraints=constraints,
        budget_hint=budget_hint if budget_hint else None,
        currency=Currency(currency),
    )

    # Step 3: Run pricing swarm
    try:
        result = await run_swarm(deal)
    except Exception as e:
        logger.exception("Swarm failed")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e), "deal": deal},
        )

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "deal": deal, "result": result},
    )
