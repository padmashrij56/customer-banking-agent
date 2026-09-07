"""Loan application lookup service - REFERENCE SOLUTION"""
import json
from pathlib import Path
from typing import Any, Dict


def load_business_data(filename: str) -> Dict[str, Any]:
    path = Path("data/business_data") / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_loan_application(application_id: str) -> Dict[str, Any]:
    data = load_business_data("loan_applications.json")
    for application in data.get("applications", []):
        if application.get("application_id") == application_id:
            return application
    return {"error": "Application not found", "application_id": application_id}
