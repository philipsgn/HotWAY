"""
Candidate models for dynamic traffic-aware multi-stop routing in Vietnam:
1. Dueling DQN with Action Masking & PER (Ablation / Retrospective Baseline)
2. Pointer Network with Bi-LSTM & A2C (Sequential Transition Baseline)
3. Attention Model (Graph Transformer Kool et al., 2019 - Proposed Core)
4. Google OR-Tools Guided Local Search (Industrial Benchmark)
"""

from models.dqn_agent import DQNAgent, DQNSolver, DuelingDQNNetwork
from models.pointer_net import PointerNetwork, PointerNetSolver
from models.attention_model import AttentionModelSolver
from models.ortools_solver import ORToolsSolver

__all__ = [
    "DQNAgent",
    "DQNSolver",
    "DuelingDQNNetwork",
    "PointerNetwork",
    "PointerNetSolver",
    "AttentionModelSolver",
    "ORToolsSolver",
]

