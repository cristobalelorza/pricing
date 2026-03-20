"""Simple JSON file storage for businesses and service templates."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from app.models import Business, ServiceTemplate

BASE_DIR = Path(__file__).resolve().parent.parent
BUSINESSES_DIR = BASE_DIR / "data" / "businesses"
SERVICES_DIR = BASE_DIR / "data" / "services"
RESULTS_DIR = BASE_DIR / "results"

BUSINESSES_DIR.mkdir(parents=True, exist_ok=True)
SERVICES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def new_id() -> str:
    return uuid.uuid4().hex[:10]


# --- Businesses ---

def list_businesses() -> list[Business]:
    businesses = []
    for path in sorted(BUSINESSES_DIR.glob("*.json")):
        try:
            businesses.append(Business(**json.loads(path.read_text())))
        except (json.JSONDecodeError, Exception):
            continue
    return businesses


def get_business(business_id: str) -> Business | None:
    path = BUSINESSES_DIR / f"{business_id}.json"
    if not path.exists():
        return None
    return Business(**json.loads(path.read_text()))


def save_business(biz: Business) -> Business:
    if not biz.id:
        biz.id = new_id()
    path = BUSINESSES_DIR / f"{biz.id}.json"
    path.write_text(json.dumps(biz.model_dump(), indent=2))
    return biz


def delete_business(business_id: str) -> bool:
    path = BUSINESSES_DIR / f"{business_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def add_pricing_run_to_business(business_id: str, result_filename: str):
    biz = get_business(business_id)
    if biz:
        biz.pricing_run_ids.append(result_filename)
        save_business(biz)


# --- Service Templates ---

def list_services() -> list[ServiceTemplate]:
    services = []
    for path in sorted(SERVICES_DIR.glob("*.json")):
        try:
            services.append(ServiceTemplate(**json.loads(path.read_text())))
        except (json.JSONDecodeError, Exception):
            continue
    return services


def get_service(service_id: str) -> ServiceTemplate | None:
    path = SERVICES_DIR / f"{service_id}.json"
    if not path.exists():
        return None
    return ServiceTemplate(**json.loads(path.read_text()))


def save_service(svc: ServiceTemplate) -> ServiceTemplate:
    if not svc.id:
        svc.id = new_id()
    path = SERVICES_DIR / f"{svc.id}.json"
    path.write_text(json.dumps(svc.model_dump(), indent=2))
    return svc


def delete_service(service_id: str) -> bool:
    path = SERVICES_DIR / f"{service_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


# --- Results ---

def list_all_results() -> list[dict]:
    """Load all saved pricing results with metadata."""
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            data["filename"] = path.name
            results.append(data)
        except (json.JSONDecodeError, Exception):
            continue
    return results


def add_note_to_result(filename: str, note: str):
    """Add/update a note on a saved result."""
    path = RESULTS_DIR / filename
    if not path.exists():
        return
    data = json.loads(path.read_text())
    data["note"] = note
    path.write_text(json.dumps(data, indent=2, default=str))

def get_business_results(business_id: str) -> list[dict]:
    """Get all pricing results linked to a business."""
    biz = get_business(business_id)
    if not biz:
        return []
    results = []
    for filename in reversed(biz.pricing_run_ids):
        path = RESULTS_DIR / filename
        if path.exists():
            try:
                data = json.loads(path.read_text())
                data["filename"] = filename
                results.append(data)
            except (json.JSONDecodeError, Exception):
                continue
    return results
