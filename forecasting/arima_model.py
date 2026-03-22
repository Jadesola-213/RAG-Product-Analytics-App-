"""
ARIMA / SARIMA forecaster using pmdarima.auto_arima.

auto_arima automatically selects the best (p,d,q)(P,D,Q)_m order
via AIC / BIC optimisation. We use m=7 for weekly seasonality.
"""

from __future__ import annotations
import logging
import numpy as np
import pandas as pd

from .base import BaseForecaster

logger = logging.getLogger(__name__)


class ARIMAForecaster(BaseForecaster):
    name = "ARIMA/SARIMA"

    def __init__(
        self,
        m: int = 7,               # seasonal period (weekly)
        max_p: int = 3,
        max_q: int = 3,
        max_P: int = 2,
        max_Q: int = 2,
    ):
        self.m     = m
        self.max_p = max_p
        self.max_q = max_q
        self.max_P = max_P
        self.max_Q = max_Q
        self._model = None
        self._last_train = None

    def fit(self, train: pd.DataFrame) -> "ARIMAForecaster":
        import pmdarima as pm
        import warnings

        y = train["y"].values
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model = pm.auto_arima(
                y,
                seasonal=True,
                m=self.m,
                max_p=self.max_p, max_q=self.max_q,
                max_P=self.max_P, max_Q=self.max_Q,
                stepwise=True,
                error_action="ignore",
                suppress_warnings=True,
                information_criterion="aic",
            )
        self._last_train = train
        logger.info("ARIMA order selected: %s", self._model.order)
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        fc, conf = self._model.predict(n_periods=horizon, return_conf_int=True)
        last_date = self._last_train["ds"].max()
        dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        return pd.DataFrame({"ds": dates, "yhat": np.clip(fc, 0, None)})
