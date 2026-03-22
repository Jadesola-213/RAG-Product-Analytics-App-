"""
Prophet forecaster.

Prophet excels at capturing weekly seasonality and holiday effects.
With ~104 days of data, yearly seasonality is disabled to avoid overfitting.
"""

from __future__ import annotations
import logging
import pandas as pd

from .base import BaseForecaster

logger = logging.getLogger(__name__)

# UK bank holidays for the prophet 'holidays' DataFrame
UK_HOLIDAYS = pd.DataFrame({
    "holiday": "uk_bank_holiday",
    "ds": pd.to_datetime([
        "2024-12-25", "2024-12-26", "2025-01-01",
        "2025-04-18", "2025-04-21", "2025-05-05",
        "2025-05-26", "2025-08-25", "2025-12-25", "2025-12-26",
    ]),
    "lower_window": 0,
    "upper_window": 1,
})


class ProphetForecaster(BaseForecaster):
    name = "Prophet"

    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
    ):
        self.changepoint_prior_scale  = changepoint_prior_scale
        self.seasonality_prior_scale  = seasonality_prior_scale
        self._model = None
        self._last_train_date = None

    def fit(self, train: pd.DataFrame) -> "ProphetForecaster":
        from prophet import Prophet  # lazy import (slow to import)
        import warnings

        self._model = Prophet(
            yearly_seasonality=False,     # only 3 months of data
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            holidays=UK_HOLIDAYS,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model.fit(train[["ds", "y"]])
        self._last_train_date = train["ds"].max()
        logger.info("Prophet fitted on %d rows.", len(train))
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        future = self._model.make_future_dataframe(periods=horizon, freq="D")
        forecast = self._model.predict(future)
        result = forecast[["ds", "yhat"]].tail(horizon).copy()
        result["yhat"] = result["yhat"].clip(lower=0)
        return result.reset_index(drop=True)
