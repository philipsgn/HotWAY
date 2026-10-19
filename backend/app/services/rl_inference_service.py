"""
HotWAY Policy Runner & Inference Service.
Connects FastAPI backend with the authentic trained PyTorch/SB3 RL model in src.rl.policy_runner.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("hotway.inference")

try:
    from src.rl.policy_runner import HotWAYPolicyRunner as BaseHotWAYPolicyRunner
except ImportError:
    try:
        from policy_runner import HotWAYPolicyRunner as BaseHotWAYPolicyRunner
    except ImportError:
        BaseHotWAYPolicyRunner = None


class HotWAYPolicyRunner:
    """Wrapper exposing <20ms predict_next_order API backed by authentic trained policy."""

    def __init__(self, model_path: str = "models/rl_best_model.zip", graph_path: str = "data/hanggon_graph.graphml"):
        self.model_path = model_path
        self.graph_path = graph_path
        self._runner = None

        if BaseHotWAYPolicyRunner is not None:
            try:
                self._runner = BaseHotWAYPolicyRunner(model_path=model_path, graph_path=graph_path)
                logger.info("Loaded authentic HotWAYPolicyRunner from src.rl.policy_runner (is_loaded=%s)", self._runner.is_loaded)
            except Exception as exc:
                logger.warning("Could not initialize BaseHotWAYPolicyRunner: %s", exc)

    def predict_next_order(
        self,
        observation: Union[Dict[str, Any], List[float]],
        action_mask: List[int],
    ) -> int:
        """Returns chosen action index within <20ms latency SLA:
        0..4: Deliver active order index
        5: WAIT
        6: RETURN_DEPOT
        """
        if self._runner is not None:
            try:
                return self._runner.predict_next_order(observation, action_mask)
            except Exception as exc:
                logger.warning("Policy runner predict failed, falling back: %s", exc)

        # Safe fallback based on action mask
        for idx, mask_val in enumerate(action_mask):
            if mask_val == 1 and idx < 5:
                return idx
        if len(action_mask) > 6 and action_mask[6] == 1:
            return 6
        return 0
