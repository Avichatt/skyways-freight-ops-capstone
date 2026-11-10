"""FastAPI service for the unloading-duration predictor."""

import os
from datetime import datetime
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SkyWays unloading-duration predictor")

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "unload_predictor.joblib"
)
LATE_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "late_arrival_predictor.joblib"
)

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Warning: could not load model from {MODEL_PATH}: {e}")

late_model = None
if os.path.exists(LATE_MODEL_PATH):
    try:
        late_model = joblib.load(LATE_MODEL_PATH)
    except Exception as e:
        print(f"Warning: could not load late model from {LATE_MODEL_PATH}: {e}")


class PredictRequest(BaseModel):
    shipment_id: str
    facility_id: str
    dock_type: str
    pallet_count: int | None = None
    load_weight_kg: int
    priority_code: str
    origin_distance_km: int = 0
    planned_departure_ts: str
    carrier_id: str
    candidate_slot_start_ts: str


class PredictResponse(BaseModel):
    model_version: str
    predicted_unload_min: int
    unload_p90_min: int
    late_arrival_probability: float = 0.0
    explanation: str


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    if model is not None:
        try:
            dep_dt = datetime.fromisoformat(req.planned_departure_ts)
            slot_dt = datetime.fromisoformat(req.candidate_slot_start_ts)

            row = {
                "dock_type": req.dock_type,
                "facility_id": req.facility_id,
                "carrier_id": req.carrier_id,
                "vehicle_type_code": "20FT",
                "product_category": "Standard freight",
                "priority_code": req.priority_code,
                "origin_city": "Delhi NCR",
                "day_of_week": slot_dt.strftime("%A"),
                "temperature_control_required": 1 if req.dock_type == "REEFER" else 0,
                "load_weight_kg": req.load_weight_kg,
                "pallet_count": req.pallet_count,
                "origin_distance_km": req.origin_distance_km,
                "rain_flag": 0,
                "labour_shortage_flag": 0,
                "departure_hour": dep_dt.hour,
                "arrival_hour": slot_dt.hour,
                "slot_hour": slot_dt.hour,
                "arrival_month": slot_dt.month,
            }

            df = pd.DataFrame([row])
            pred_val = float(model.predict(df)[0])
            pred_min = max(20, int(round(pred_val)))
            p90_min = pred_min + 14

            late_prob = 0.0
            if late_model is not None:
                try:
                    late_prob = float(late_model.predict_proba(df)[0][1])
                except Exception:
                    pass

            return PredictResponse(
                model_version="rf-2026-08-04",
                predicted_unload_min=pred_min,
                unload_p90_min=p90_min,
                late_arrival_probability=round(late_prob, 2),
                explanation=f"Predicted {pred_min}m (p90: {p90_min}m, late risk: {late_prob:.0%}) based on {req.dock_type} dock and {req.load_weight_kg}kg load."
            )
        except Exception:
            pass

    default_pred = 45 if req.dock_type == "STANDARD" else 60
    return PredictResponse(
        model_version="stub-fallback",
        predicted_unload_min=default_pred,
        unload_p90_min=default_pred + 15,
        late_arrival_probability=0.2,
        explanation="Default facility estimate (fallback)."
    )