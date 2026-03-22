"""
LSTM forecaster built with PyTorch.

Architecture: 2-layer stacked LSTM → Linear readout.
Training:     Adam + MSE loss + early stopping (patience=20).
Inference:    recursive multi-step prediction with MinMax scaling.

Note: With ~104 days of data, LSTM results carry higher variance than
      statistical models. Results are included for comparison purposes.
"""

from __future__ import annotations
import logging
import numpy as np
import pandas as pd

from .base import BaseForecaster
from config import LSTM_SEQ_LEN, LSTM_EPOCHS, LSTM_HIDDEN, LSTM_LAYERS, LSTM_DROPOUT, LSTM_LR

logger = logging.getLogger(__name__)


def _make_sequences(values: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(len(values) - seq_len):
        X.append(values[i : i + seq_len])
        y.append(values[i + seq_len])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


class _LSTMNet:
    """Thin wrapper so we only import torch inside methods."""

    def __init__(self, hidden: int, layers: int, dropout: float):
        import torch
        import torch.nn as nn

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(
                    input_size=1, hidden_size=hidden,
                    num_layers=layers, dropout=dropout if layers > 1 else 0,
                    batch_first=True,
                )
                self.fc = nn.Linear(hidden, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :]).squeeze(-1)

        self.net    = Net()
        self.device = torch.device("cpu")

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int, lr: float):
        import torch
        import torch.nn as nn

        Xt = torch.tensor(X).unsqueeze(-1)
        yt = torch.tensor(y)
        opt  = torch.optim.Adam(self.net.parameters(), lr=lr)
        loss_fn = nn.MSELoss()

        best_loss, patience, wait = np.inf, 20, 0
        best_state = None

        self.net.train()
        for epoch in range(epochs):
            opt.zero_grad()
            pred = self.net(Xt)
            loss = loss_fn(pred, yt)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
            opt.step()

            val = loss.item()
            if val < best_loss - 1e-5:
                best_loss  = val
                best_state = {k: v.clone() for k, v in self.net.state_dict().items()}
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    logger.debug("LSTM early stop at epoch %d", epoch)
                    break

        if best_state:
            self.net.load_state_dict(best_state)

    def predict_one(self, seq: np.ndarray) -> float:
        import torch
        self.net.eval()
        with torch.no_grad():
            t = torch.tensor(seq, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            return float(self.net(t).item())


class LSTMForecaster(BaseForecaster):
    name = "LSTM"

    def __init__(
        self,
        seq_len: int  = LSTM_SEQ_LEN,
        hidden:  int  = LSTM_HIDDEN,
        layers:  int  = LSTM_LAYERS,
        dropout: float= LSTM_DROPOUT,
        epochs:  int  = LSTM_EPOCHS,
        lr:      float= LSTM_LR,
    ):
        self.seq_len = seq_len
        self._net    = _LSTMNet(hidden, layers, dropout)
        self._epochs = epochs
        self._lr     = lr
        self._scaler_min = 0.0
        self._scaler_rng = 1.0
        self._last_seq   = None
        self._last_date  = None

    # ── scaling helpers ───────────────────────────────────────────────────────
    def _scale(self, v):   return (v - self._scaler_min) / self._scaler_rng
    def _unscale(self, v): return v * self._scaler_rng + self._scaler_min

    def fit(self, train: pd.DataFrame) -> "LSTMForecaster":
        y = train["y"].values.astype(np.float32)
        self._scaler_min = y.min()
        self._scaler_rng = max(y.max() - y.min(), 1e-6)
        y_norm = self._scale(y)

        if len(y_norm) < self.seq_len + 1:
            logger.warning(
                "LSTM: only %d data points, need >%d. Reducing seq_len.", len(y_norm), self.seq_len
            )
            self.seq_len = max(3, len(y_norm) // 2)

        X, targets = _make_sequences(y_norm, self.seq_len)
        self._net.fit(X, targets, self._epochs, self._lr)
        self._last_seq  = y_norm[-self.seq_len:].tolist()
        self._last_date = train["ds"].max()
        logger.info("LSTM fitted on %d samples (seq_len=%d).", len(X), self.seq_len)
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        seq = list(self._last_seq)
        preds = []
        for _ in range(horizon):
            arr  = np.array(seq[-self.seq_len:], dtype=np.float32)
            yhat = self._net.predict_one(arr)
            preds.append(max(0.0, self._unscale(yhat)))
            seq.append(yhat)

        dates = pd.date_range(self._last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        return pd.DataFrame({"ds": dates, "yhat": preds})
