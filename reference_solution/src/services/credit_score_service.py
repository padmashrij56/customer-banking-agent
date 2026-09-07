"""Credit bureau lookup service - REFERENCE SOLUTION"""
import json
from pathlib import Path
from typing import Any, Dict


def load_business_data(filename: str) -> Dict[str, Any]:
    path = Path("data/business_data") / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_credit_score(customer_id: str) -> Dict[str, Any]:
    data = load_business_data("credit_scores.json")
    for record in data.get("credit_scores", []):
        if record.get("customer_id") == customer_id:
            return record
    return {"error": "Credit record not found", "customer_id": customer_id}
