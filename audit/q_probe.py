"""Probe initial Q-values of audit checkpoints on the test split."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "audit"))

from audit.benchmark_audit import install_weight_map  # noqa: E402
from src.benchmark.instance_generator import load_benchmark_instances  # noqa: E402
from src.cvrp_solver.constructive import clarke_wright_savings  # noqa: E402
from src.cvrp_solver.q_network import QNetworkInference  # noqa: E402
from src.cvrp_solver.state_f28 import compute_f28_state  # noqa: E402
from src.cvrp_solver.validator import calculate_route_distance  # noqa: E402

OUT = ROOT / "audit" / "results" / "q_probe.json"
NAMES = ["two_opt", "intra_relocate", "inter_relocate", "inter_swap"]


def main() -> None:
    instances = [i for i in load_benchmark_instances(ROOT / "data" / "benchmark_instances") if int(i.name[-2:]) >= 25]
    wdir = ROOT / "audit" / "weights"
    records = []
    for algo in ["dqn", "double_dqn"]:
        install_weight_map({
            "src/cvrp_solver/weights/dqn_model.pt": str(wdir / f"fair_dqn_best.pt"),
            "src/cvrp_solver/weights/double_dqn_model.pt": str(wdir / f"fair_double_dqn_best.pt"),
        })
        model = QNetworkInference(
            weights_path=str(wdir / f"fair_{algo}_best.pt"),
            seed=2027,
        )
        for inst in instances:
            routes = clarke_wright_savings(inst)
            cost = sum(calculate_route_distance(r, inst.dist_matrix) for r in routes)
            state = compute_f28_state(
                routes, cost, cost, cost, 1, 100, 0, 30,
                [0, 0, 0, 0], [0, 0, 0, 0], -1, False, inst,
            )
            q = model.predict_q_values(np.asarray(state, dtype=np.float32))
            records.append({
                "algorithm": "DQN" if algo == "dqn" else "Double DQN",
                "instance_id": inst.name,
                "q_values": [round(float(x), 4) for x in q],
                "argmax": int(np.argmax(q)),
                "argmax_operator": NAMES[int(np.argmax(q))],
                "q_spread": round(float(q.max() - q.min()), 4),
            })

    by_algo = {}
    for name in ["DQN", "Double DQN"]:
        rows = [r for r in records if r["algorithm"] == name]
        by_algo[name] = {
            "mean_q": [round(float(np.mean([r["q_values"][i] for r in rows])), 4) for i in range(4)],
            "argmax_counts": {
                NAMES[i]: sum(1 for r in rows if r["argmax"] == i) for i in range(4)
            },
            "mean_q_spread": round(float(np.mean([r["q_spread"] for r in rows])), 4),
        }
    report = {"operators": NAMES, "summary": by_algo, "records": records}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
