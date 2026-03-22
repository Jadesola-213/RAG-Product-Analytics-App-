"""
Abstract base class for all forecasting models.
Every concrete model must implement fit() and predict().
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd


class BaseForecaster(ABC):
    """
    All forecasters receive a daily time series DataFrame with at least
    columns ['ds', 'y'] (date, target value) and return a DataFrame with
    columns ['ds', 'yhat'] for the forecast horizon.
    """

    name: str = "BaseForecaster"

    @abstractmethod
    def fit(self, train: pd.DataFrame) -> "BaseForecaster":
        """Fit the model on *train* (columns: ds, y)."""
        ...

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """
        Produce *horizon* day-ahead forecasts.
        Returns DataFrame with columns ['ds', 'yhat'].
        """
        ...

    def fit_predict(self, train: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self.fit(train)
        return self.predict(horizon)
