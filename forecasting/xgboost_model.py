"""
XGBoost forecaster using lag + rolling features.

Treats time series forecasting as a supervised regression problem.
At inference time, predictions are made recursively: each predicted
value feeds back as a lag feature for subsequent steps.
"""

from __future__ import annotations
import logging
import numpy as np
import pandas as pd

from .base import BaseForecaster

logger = logging.getLogger(__name__)

LAGS     = [1, 2, 3, 7, 14]
ROLL_WIN = [7, 14]


def _make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag, rolling, and calendar features to a daily series."""
    df = df.copy().sort_values("ds").reset_index(drop=True)
    df["dow"]     = df["ds"].dt.dayofweek
    df["month"]   = df["ds"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    for lag in LAGS:
        df[f"lag_{lag}"] = df["y"].shift(lag)

    for w in ROLL_WIN:
        df[f"roll_mean_{w}"] = df["y"].shift(1).rolling(w).mean()
        df[f"roll_std_{w}"]  = df["y"].shift(1).rolling(w).std()

    return df


FEATURE_COLS = (
    ["dow", "month", "is_weekend"]
    + [f"lag_{l}"        for l in LAGS]
    + [f"roll_mean_{w}"  for w in ROLL_WIN]
    + [f"roll_std_{w}"   for w in ROLL_WIN]
)


class XGBoostForecaster(BaseForecaster):
    name = "XGBoost"

    def __init__(self, n_estimators: int = 300, max_depth: int = 4, lr: float = 0.05):
        self.n_estimators = n_estimators
        self.max_depth    = max_depth
        self.lr           = lr
        self._model       = None
        self._train       = None   # kept for recursive prediction

    def fit(self, train: pd.DataFrame) -> "XGBoostForecaster":
        from xgboost import XGBRegressor

        feat = _make_features(train).dropna(subset=FEATURE_COLS)
        X = feat[FEATURE_COLS]
        y = feat["y"]

        self._model = XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.lr,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        self._model.fit(X, y)
        self._train = train.copy()
        logger.info("XGBoost fitted on %d rows.", len(feat))
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        # Recursive multi-step prediction
        history = self._train["y"].tolist()
        last_date = self._train["ds"].max()
        preds = []

        for step in range(horizon):
            future_date = last_date + pd.Timedelta(days=step + 1)
            row = {
                "dow":       future_date.dayofweek,
                "month":     future_date.month,
                "is_weekend": int(future_date.dayofweek >= 5),
            }
            for lag in LAGS:
                idx = -(lag)
                row[f"lag_{lag}"] = history[idx] if len(history) >= lag else 0.0
            for w in ROLL_WIN:
                window = history[-w:] if len(history) >= w else history
                row[f"roll_mean_{w}"] = float(np.mean(window)) if window else 0.0
                row[f"roll_std_{w}"]  = float(np.std(window))  if window else 0.0

            X_row = pd.DataFrame([row])[FEATURE_COLS]
            yhat  = float(self._model.predict(X_row)[0])
            yhat  = max(0, yhat)
            preds.append(yhat)
            history.append(yhat)

        dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        return pd.DataFrame({"ds": dates, "yhat": preds})
