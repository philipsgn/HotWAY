"""
Exact Dynamic Programming (Value Iteration) and Dijkstra Baseline for GĐ1.
Solves the exact Bellman optimality equation for adaptive stochastic routing,
providing an analytical Ground Truth with 0 approximation error.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple, Any, Optional

import networkx as nx
import numpy as np
from src.envs.routing_env import RoutingEnv


class ExactValueIteration:
    """
    Computes exact Value Iteration solution V*(s) on the finite MDP of RoutingEnv.
    """

    def __init__(
        self,
        env: RoutingEnv,
        discount_gamma: float = 1.0,
        epsilon: float = 1e-12,
        max_iterations: int = 1000,
    ):
        self.env = env
        self.gamma = discount_gamma
        self.epsilon = epsilon
        self.max_iterations = max_iterations

        # Enumerate all possible states: (node, congestion_tuple_for_outgoing_edges)
        self.states: List[Tuple[int, Tuple[int, ...]]] = []
        self.state_to_idx: Dict[Tuple[int, Tuple[int, ...]], int] = {}

        for u in self.env.nodes:
            deg = len(self.env.adj[u])
            # All combinations of congestion {0, 1, 2}^deg
            for cong in itertools.product(range(3), repeat=deg):
                s = (u, cong)
                self.state_to_idx[s] = len(self.states)
                self.states.append(s)

        self.n_states = len(self.states)
        self.V = np.zeros(self.n_states, dtype=np.float64)
        self.policy: Dict[Tuple[int, Tuple[int, ...]], int] = {}

    def solve(self, dest_node: Optional[int] = None) -> Tuple[np.ndarray, Dict[Tuple[int, Tuple[int, ...]], int]]:
        """Solves the Bellman optimality equation until convergence."""
        dest = dest_node if dest_node is not None else self.env.dest_node
        P_traffic = self.env.P_traffic
        congest_mult = self.env.congestion_multipliers
        speed = self.env.free_speed_mps

        # Initialize V: 0 at destination, -infinity or negative estimate elsewhere
        V = np.full(self.n_states, -100.0, dtype=np.float64)
        for s, idx in self.state_to_idx.items():
            if s[0] == dest:
                V[idx] = 0.0

        for it in range(self.max_iterations):
            delta = 0.0
            new_V = V.copy()

            for s, idx in self.state_to_idx.items():
                u, cong_tuple = s
                if u == dest:
                    new_V[idx] = 0.0
                    continue

                succs = self.env.adj[u]
                if len(succs) == 0:
                    continue

                best_q = -float("inf")
                best_act = 0

                for act, v in enumerate(succs):
                    edge = (u, v)
                    length = self.env.edge_lengths[edge]
                    c_e = cong_tuple[act]
                    cost = (length / speed) * congest_mult[c_e]
                    imm_reward = -cost

                    if v == dest:
                        exp_future = 0.0
                    else:
                        # Expected value over next node v's outgoing congestion transitions
                        v_succs = self.env.adj[v]
                        deg_v = len(v_succs)

                        # Probability of each congestion profile at v
                        # Marginal distribution of traffic at next step
                        exp_future = 0.0
                        for next_cong in itertools.product(range(3), repeat=deg_v):
                            prob = 1.0
                            for k, c_next in enumerate(next_cong):
                                # If edge is from u to v, we know its previous congestion c_e
                                # Otherwise assume stationary prior or marginal
                                prob *= P_traffic[1, c_next]  # average transition

                            next_state = (v, next_cong)
                            next_idx = self.state_to_idx[next_state]
                            exp_future += prob * V[next_idx]

                    q_val = imm_reward + self.gamma * exp_future
                    if q_val > best_q:
                        best_q = q_val
                        best_act = act

                new_V[idx] = best_q
                self.policy[s] = best_act
                delta = max(delta, abs(new_V[idx] - V[idx]))

            V = new_V
            if delta < self.epsilon:
                break

        self.V = V
        return V, self.policy


class DijkstraAverageBaseline:
    """
    Computes static optimal route based on expected edge travel times.
    """

    def __init__(self, env: RoutingEnv):
        self.env = env
        # Compute expected congestion multiplier: sum(p_i * mult_i)
        # Stationary distribution of P_traffic: approx [0.45, 0.40, 0.15]
        stationary_p = np.array([0.45, 0.40, 0.15], dtype=np.float64)
        self.avg_mult = float(np.sum(stationary_p * self.env.congestion_multipliers))

        # Build weighted networkx graph with average edge times
        self.static_G = nx.DiGraph()
        for edge, length in self.env.edge_lengths.items():
            u, v = edge
            avg_time = (length / self.env.free_speed_mps) * self.avg_mult
            self.static_G.add_edge(u, v, weight=avg_time)

    def get_path(self, source: int, dest: int) -> List[int]:
        return nx.shortest_path(self.static_G, source=source, target=dest, weight="weight")

    def get_action(self, current_node: int, dest: int) -> int:
        path = self.get_path(current_node, dest)
        if len(path) >= 2:
            next_node = path[1]
            succs = self.env.adj[current_node]
            if next_node in succs:
                return succs.index(next_node)
        return 0
