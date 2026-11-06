"""FastAPI stub for the unloading-duration predictor."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SkyWays unloading-duration predictor")


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
    explanation: str


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    # TODO: Load the trained model once at startup.
    # Until then, return a placeholder estimate.
    return PredictResponse(
        model_version="stub-0",
        predicted_unload_min=60,
        unload_p90_min=75,
        explanation="Stub prediction: facility default estimate."
    )