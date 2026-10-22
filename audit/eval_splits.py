"""Evaluate retrained checkpoints on train/validation/test splits under protocol A."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "audit"))

from audit.benchmark_audit import install_weight_map  # noqa: E402
from src.benchmark.instance_generator import load_benchmark_instances  # noqa: E402
from src.cvrp_solver.search import solve_cvrp_strategy  # noqa: E402

OUT_JSON = ROOT / "audit" / "results" / "eval_splits.json"
OUT_CSV = ROOT / "audit" / "results" / "eval_splits.csv"


def split_of(idx: int) -> str:
    if idx <= 20:
        return "train"
    if idx <= 24:
        return "validation"
    return "test"


def main() -> None:
    instances = load_benchmark_instances(ROOT / "data" / "benchmark_instances")
    wdir = ROOT / "audit" / "weights"
    rows = []
    for tag in ["repro", "fair"]:
        for suffix in ["best", "final"]:
            install_weight_map({
                "src/cvrp_solver/weights/dqn_model.pt": str(wdir / f"{tag}_dqn_{suffix}.pt"),
                "src/cvrp_solver/weights/double_dqn_model.pt": str(wdir / f"{tag}_double_dqn_{suffix}.pt"),
            })
            for inst in instances:
                idx = int(inst.name[-2:])
                for strategy in ["dqn", "double_dqn"]:
                    sol = solve_cvrp_strategy(
                        strategy=strategy,
                        instance=inst,
                        max_steps=100,
                        max_candidates=128,
                        seed=2027,
                    )
                    rows.append({
                        "tag": tag,
                        "suffix": suffix,
                        "strategy": "DQN" if strategy == "dqn" else "Double DQN",
                        "instance_id": inst.name,
                        "split": split_of(idx),
                        "cost_km": round(sol.total_distance / 1000.0, 4),
                    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    summary = (
        df.groupby(["tag", "suffix", "strategy", "split"])["cost_km"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .round(4)
    )
    report = {
        "protocol": {"max_steps": 100, "max_candidates": 128},
        "seed": 2027,
        "summary": summary.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
