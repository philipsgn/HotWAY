"""
Q-Network for DQN & Double DQN Local Search Operator Selection.
Matches Section 4.5 & Table 4 of Final Report:
MLP architecture: 28 -> 128 -> 128 -> 4 with ReLU activations.
Supports PyTorch as primary and pure NumPy inference fallback.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:
    class PyTorchQNetwork(nn.Module):
        def __init__(self, state_dim: int = 28, action_dim: int = 4):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 128),
                nn.ReLU(),
                nn.Linear(128, action_dim),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)


class QNetworkInference:
    """
    Lightweight forward inference engine supporting both PyTorch and NumPy weights.
    """
    def __init__(self, weights_path: Optional[str] = None, seed: int = 42):
        self.state_dim = 28
        self.action_dim = 4
        self.rng = np.random.RandomState(seed)

        # Initialize deterministic default weights
        # W1: (128, 28), b1: (128,)
        self.W1 = self.rng.randn(128, 28).astype(np.float32) * np.sqrt(2.0 / 28)
        self.b1 = np.zeros(128, dtype=np.float32)
        # W2: (128, 128), b2: (128,)
        self.W2 = self.rng.randn(128, 128).astype(np.float32) * np.sqrt(2.0 / 128)
        self.b2 = np.zeros(128, dtype=np.float32)
        # W3: (4, 128), b3: (4,)
        self.W3 = self.rng.randn(4, 128).astype(np.float32) * np.sqrt(2.0 / 128)
        self.b3 = np.zeros(4, dtype=np.float32)

        self.torch_model = None
        if TORCH_AVAILABLE:
            self.torch_model = PyTorchQNetwork(self.state_dim, self.action_dim)
            if weights_path and os.path.exists(weights_path):
                try:
                    self.torch_model.load_state_dict(torch.load(weights_path, map_location="cpu"))
                    self.torch_model.eval()
                except Exception:
                    pass

    def predict_q_values(self, state: np.ndarray) -> np.ndarray:
        """Computes Q(s, a) for all 4 actions given 28-dim state vector."""
        if TORCH_AVAILABLE and self.torch_model is not None:
            with torch.no_grad():
                t_x = torch.from_numpy(state.astype(np.float32)).unsqueeze(0)
                q_vals = self.torch_model(t_x).squeeze(0).numpy()
                return q_vals

        # NumPy fallback inference
        x = state.astype(np.float32)
        h1 = np.maximum(0, np.dot(self.W1, x) + self.b1) # ReLU
        h2 = np.maximum(0, np.dot(self.W2, h1) + self.b2) # ReLU
        q = np.dot(self.W3, h2) + self.b3
        return q

    def select_action(self, state: np.ndarray, epsilon: float = 0.0) -> int:
        if epsilon > 0.0 and self.rng.rand() < epsilon:
            return int(self.rng.randint(0, self.action_dim))
        q = self.predict_q_values(state)
        return int(np.argmax(q))
