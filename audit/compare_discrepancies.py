"""Compare the shipped rel_result benchmark against an independent stock rerun.

Produces audit/results/discrepancy_report_all.json and discrepancy_raw_compare_all.csv.
The comparison covers all 30 instances with stock weights/seed 42, so it isolates
methodology errors from model-quality differences; the test split is also reported.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHIPPED = ROOT / "rel_result" / "raw_runs.csv"
AUDIT = ROOT / "audit" / "results" / "raw_runs_stock_all_seed42.csv"
OUT_JSON = ROOT / "audit" / "results" / "discrepancy_report_all.json"
OUT_CSV = ROOT / "audit" / "results" / "discrepancy_raw_compare_all.csv"

PROTOCOLS = ["A2", "A", "A3", "B", "B2"]
LIMITS = {"A2": None, "A": None, "A3": None, "B": 0.05, "B2": 0.10}
TEST_IDS = [f"HCMC_VN_{i:02d}" for i in range(25, 31)]


def _round(x, n=6):
    return round(float(x), n)


def main() -> None:
    shipped = pd.read_csv(SHIPPED)
    audit = pd.read_csv(AUDIT)

    if "seed" in audit.columns:
        audit = audit[audit["seed"] == 42].copy()

    keys = ["instance_id", "strategy", "protocol"]
    merged = shipped.merge(
        audit,
        on=keys,
        suffixes=("_shipped", "_audit"),
        validate="one_to_one",
    )
    merged["delta_cost_km"] = merged["cost_km_audit"] - merged["cost_km_shipped"]
    merged["delta_improvement_pct"] = (
        merged["improvement_pct_audit"] - merged["improvement_pct_shipped"]
    )
    merged["eval_ratio"] = merged["evals_actual"] / merged["evals"].replace(0, np.nan)
    merged["runtime_ratio"] = merged["runtime_sec_audit"] / merged["runtime_sec_shipped"].replace(0, np.nan)
    merged.to_csv(OUT_CSV, index=False)

    eval_compare = {
        "rows_compared": int(len(merged)),
        "shipped_evals_total": int(merged["evals"].sum()),
        "audit_evals_actual_total": int(merged["evals_actual"].sum()),
        "actual_over_shipped_ratio": _round(
            merged["evals_actual"].sum() / max(merged["evals"].sum(), 1)
        ),
        "shipped_evals_mean": _round(merged["evals"].mean(), 1),
        "audit_evals_actual_mean": _round(merged["evals_actual"].mean(), 1),
        "rows_with_exact_fabrication_formula": int(
            (
                merged["evals"]
                == merged["decisions"] * merged["candidates_budget"]
            ).sum()
        ),
        "eval_ratio_min": _round(merged["eval_ratio"].min()),
        "eval_ratio_median": _round(merged["eval_ratio"].median()),
        "eval_ratio_max": _round(merged["eval_ratio"].max()),
    }

    time_rows = merged[merged["protocol"].isin(["B", "B2"])].copy()
    time_rows["limit"] = time_rows["protocol"].map(LIMITS)
    time_rows["overrun_sec"] = time_rows["runtime_sec_shipped"] - time_rows["limit"]
    time_compare = {
        "rows_B_B2": int(len(time_rows)),
        "violations_over_limit": int((time_rows["overrun_sec"] > 0).sum()),
        "violation_rate": _round((time_rows["overrun_sec"] > 0).mean()),
        "max_overrun_sec": _round(time_rows["overrun_sec"].max()),
        "max_overrun_factor": _round(
            (time_rows["runtime_sec_shipped"] / time_rows["limit"]).max()
        ),
        "median_runtime_sec": _round(time_rows["runtime_sec_shipped"].median()),
        "max_runtime_sec": _round(time_rows["runtime_sec_shipped"].max()),
        "note": "Shipped runner ignores time_limit_sec; audit --enforce-time hit the deadline on every B/B2 run.",
    }

    a = shipped[shipped["protocol"] == "A"].set_index(["instance_id", "strategy"])
    a3 = shipped[shipped["protocol"] == "A3"].set_index(["instance_id", "strategy"])
    common = a.index.intersection(a3.index)
    a3_compare = {
        "paired_rows": int(len(common)),
        "cost_identical_rate": _round(
            float(np.mean(np.isclose(a.loc[common, "cost_km"], a3.loc[common, "cost_km"], atol=1e-12)))
        ),
        "evals_identical_rate": _round(
            float(np.mean(a.loc[common, "evals"].values == a3.loc[common, "evals"].values))
        ),
        "max_abs_cost_delta_km": _round(
            float(np.max(np.abs(a.loc[common, "cost_km"].values - a3.loc[common, "cost_km"].values)))
        ),
        "note": "Protocol A and A3 are identical code paths (same max_steps/max_candidates; feature_patience unused).",
    }

    thermal = {
        "rows": int(len(shipped)),
        "capacity_fleet_feasible_rate": _round(shipped["feasible"].mean()),
        "rows_with_thermal_violations": int((shipped["thermal_violations"] > 0).sum()),
        "thermal_violation_rate": _round((shipped["thermal_violations"] > 0).mean()),
        "mean_thermal_violations": _round(shipped["thermal_violations"].mean(), 2),
        "min_delivery_temp_c": _round(shipped["min_delivery_temp_c"].min(), 1),
        "note": "Shipped feasible_rate only checks capacity/fleet/coverage; validator ignores thermal constraints.",
    }

    identity_groups = (
        audit.groupby(["protocol", "instance_id", "seed"])["cost_km"]
        .nunique()
        .reset_index(name="n_distinct_costs")
    )
    identity = {
        "groups": int(len(identity_groups)),
        "groups_all_five_equal": int((identity_groups["n_distinct_costs"] == 1).sum()),
        "all_five_equal_rate": _round((identity_groups["n_distinct_costs"] == 1).mean()),
        "mean_distinct_costs_among_five": _round(identity_groups["n_distinct_costs"].mean(), 3),
    }

    applied = (
        audit.groupby("strategy")["applied_steps"]
        .agg(["mean", "max"])
        .reset_index()
        .rename(columns={"mean": "mean_applied_steps", "max": "max_applied_steps"})
    )
    applied_stats = {
        row["strategy"]: {
            "mean_applied_steps": _round(row["mean_applied_steps"], 2),
            "max_applied_steps": int(row["max_applied_steps"]),
        }
        for _, row in applied.iterrows()
    }

    actions = {}
    for strategy in ["DQN", "Double DQN"]:
        s = audit[audit["strategy"] == strategy]
        if s.empty:
            continue
        actions[strategy] = {
            proto: {
                "n_runs": int(len(sub)),
                "mean_action_share": [
                    _round(sub[f"action_{i}"].sum() / max(sub[["action_0", "action_1", "action_2", "action_3"]].sum().sum(), 1), 4)
                    for i in range(4)
                ],
            }
            for proto, sub in s.groupby("protocol")
        }

    training = {
        "instances_loaded_by_stock_trainer": 30,
        "test_instances_used_in_training": 6,
        "test_leak_rate": _round(6 / 30),
        "train_instances_expected": 20,
        "validation_instances_expected": 4,
        "test_instances_expected": 6,
        "validation_split_implemented": False,
        "validation_checkpoint_selection_implemented": False,
        "audit_best_val_cost_km": {"dqn": 92.871, "double_dqn": 92.871},
        "audit_best_episode": {"dqn": 1, "double_dqn": 10},
        "audit_episodes": 150,
        "note": "Best validation checkpoint is an early/untrained policy; validation set has only 4 instances.",
    }

    stats = {
        "shipped_summary": {
            "mean_distance_km": _round(shipped["cost_km"].mean(), 4),
            "mean_improvement_pct": _round(shipped["improvement_pct"].mean(), 4),
            "rows": int(len(shipped)),
        },
        "audit_summary": {
            "mean_distance_km": _round(audit["cost_km"].mean(), 4),
            "mean_improvement_pct": _round(audit["improvement_pct"].mean(), 4),
            "rows": int(len(audit)),
        },
        "by_strategy_shipped": {
            k: {
                "mean_distance_km": _round(v["cost_km"].mean(), 4),
                "mean_improvement_pct": _round(v["improvement_pct"].mean(), 4),
            }
            for k, v in shipped.groupby("strategy")
        },
        "by_strategy_audit": {
            k: {
                "mean_distance_km": _round(v["cost_km"].mean(), 4),
                "mean_improvement_pct": _round(v["improvement_pct"].mean(), 4),
            }
            for k, v in audit.groupby("strategy")
        },
    }

    report = {
        "keys": keys,
        "cost_reproduction": {
            "rows_compared": int(len(merged)),
            "max_abs_delta_cost_km": _round(merged["delta_cost_km"].abs().max()),
            "max_abs_delta_improvement_pct": _round(merged["delta_improvement_pct"].abs().max()),
            "within_1m": int((merged["delta_cost_km"].abs() < 0.001).sum()),
            "test_subset": {
                "rows": int(len(merged[merged["instance_id"].isin(TEST_IDS)])),
                "max_abs_delta_cost_km": _round(
                    merged[merged["instance_id"].isin(TEST_IDS)]["delta_cost_km"].abs().max()
                ),
            },
        },
        "eval_fabrication": eval_compare,
        "time_budget": time_compare,
        "protocol_A_vs_A3": a3_compare,
        "thermal": thermal,
        "strategy_identity": identity,
        "applied_steps": applied_stats,
        "action_distribution": actions,
        "training_leakage": training,
        "stats": stats,
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
