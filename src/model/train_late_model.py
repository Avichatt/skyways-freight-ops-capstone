"""
Backward-compatibility forwarder.
Re-exports from src.model.train_hist_gradient_boosting.
"""

from src.model.train_hist_gradient_boosting import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    HistGradientBoostingPipeline,
    LateArrivalPredictorPipeline,
    build_and_train_hist_gradient_boosting,
    build_and_train_late_model,
)

if __name__ == "__main__":
    build_and_train_hist_gradient_boosting()

