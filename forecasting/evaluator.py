"""
Backtesting engine and forecast runner.

run_backtest()  → hold-out last N days, train each model, return metrics
run_forecast()  → train all selected models on full data, return future predictions
"""

from __future__ import annotations
import logging
import traceback
from typing import Sequence

import numpy as np
import pandas as pd

from config import BACKTEST_WINDOW, FORECAST_MODELS
from .prophet_model  import ProphetForecaster
from .arima_model    import ARIMAForecaster
from .xgboost_model  import XGBoostForecaster
from .lstm_model     import LSTMForecaster

logger = logging.getLogger(__name__)

_MODEL_REGISTRY = {
    "Prophet":      ProphetForecaster,
    "ARIMA/SARIMA": ARIMAForecaster,
    "XGBoost":      XGBoostForecaster,
    "LSTM":         LSTMForecaster,
}


def _mape(actual: np.ndarray, pred: np.ndarray) -> float:
    mask = actual != 0
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100)


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    mae  = float(np.mean(np.abs(actual - pred)))
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
    mape = _mape(actual, pred)
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE (%)": round(mape, 2)}


def run_backtest(
    series: pd.DataFrame,
    models: Sequence[str] = FORECAST_MODELS,
    window: int = BACKTEST_WINDOW,
) -> pd.DataFrame:
    """
    Hold out the last *window* days as a test set.
    Train each requested model on the remaining data.
    Return a DataFrame: model | MAE | RMSE | MAPE (%)
    """
    if len(series) < window + 10:
        window = max(3, len(series) // 5)
        logger.warning("Short series: reducing backtest window to %d.", window)

    train = series.iloc[:-window]
    test  = series.iloc[-window:]
    actual = test["y"].values

    rows = []
    for name in models:
        cls = _MODEL_REGISTRY.get(name)
        if cls is None:
            continue
        try:
            model = cls()
            pred_df = model.fit_predict(train, window)
            pred = pred_df["yhat"].values
            m = _metrics(actual, pred)
            m["Model"] = name
            rows.append(m)
            logger.info("Backtest [%s]: MAE=%.2f RMSE=%.2f MAPE=%.1f%%",
                        name, m["MAE"], m["RMSE"], m["MAPE (%)"])
        except Exception:
            logger.error("Backtest failed for %s:\n%s", name, traceback.format_exc())
            rows.append({"Model": name, "MAE": None, "RMSE": None, "MAPE (%)": None})

    return pd.DataFrame(rows, columns=["Model", "MAE", "RMSE", "MAPE (%)"])


def run_forecast(
    series: pd.DataFrame,
    horizon: int,
    models: Sequence[str] = FORECAST_MODELS,
) -> dict[str, pd.DataFrame]:
    """
    Train each model on the full series and forecast *horizon* days ahead.
    Returns dict: model_name → DataFrame(ds, yhat)
    """
    results = {}
    for name in models:
        cls = _MODEL_REGISTRY.get(name)
        if cls is None:
            continue
        try:
            model = cls()
            pred_df = model.fit_predict(series, horizon)
            results[name] = pred_df
            logger.info("Forecast [%s] done: %d steps.", name, horizon)
        except Exception:
            logger.error("Forecast failed for %s:\n%s", name, traceback.format_exc())
    return results
