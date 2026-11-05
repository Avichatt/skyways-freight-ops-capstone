"""FastAPI stub for the predictor. Run: uvicorn predict_service_stub:app --reload --port 8010

Fill `predict` with your trained model. Keep the request and response shapes exactly as in integration_contract.md.
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SkyWays predictor")


class PredictRequest(BaseModel):
    shipment_id: str
    facility_id: str
    dock_type: str
    pallet_count: int | None
    load_weight_kg: int
    priority_code: str
    origin_distance_km: int
    planned_departure_ts: str
    carrier_id: str
    candidate_slot_start_ts: str


class PredictResponse(BaseModel):
    model_version: str
    predicted_unload_min: int
    unload_p90_min: int
    late_arrival_probability: float
    explanation: str


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    # TODO: load your model once at startup (not per request), build the feature row, predict.
    # Until then this returns the facility default so the agent can be developed in parallel.
    return PredictResponse(model_version="stub-0", predicted_unload_min=60, unload_p90_min=75,
                           late_arrival_probability=0.3, explanation="stub: facility default")
