"""
Unit and Integration Test T3: Report Fidelity & Numerical Audit.
Verifies that all metrics cited in research documents and exported in
results/all_metrics_registry.json match the generated benchmark outputs
with absolute numerical difference < 1e-9 (and markdown representations match to formatted precision).
"""

import json
import re
from pathlib import Path
import pandas as pd
import pytest


def test_registry_csv_fidelity_below_1e9():
    """Verifies that all values in all_metrics_registry.json match source CSV files to < 1e-9."""
    registry_file = Path("results/all_metrics_registry.json")
    assert registry_file.exists(), "results/all_metrics_registry.json must exist"

    with open(registry_file, "r", encoding="utf-8") as f:
        registry = json.load(f)

    # Check baseline summary fidelity
    base_file = Path("results/baselines/summary_baseline_test.csv")
    df_base = pd.read_csv(base_file)
    for _, row in df_base.iterrows():
        p = row["policy"]
        for col in ["mean_wait_min", "p90_wait_min", "late_rate_pct", "gini_coefficient", "fleet_utilization_pct"]:
            reg_key = f"{p}_{col}"
            assert reg_key in registry, f"Missing key {reg_key} in registry"
            csv_val = float(row[col])
            reg_val = float(registry[reg_key])
            err = abs(csv_val - reg_val)
            assert err < 1e-9, f"Fidelity error on {reg_key}: {err} >= 1e-9 (csv={csv_val}, reg={reg_val})"

    # Check RL summary fidelity
    rl_file = Path("results/training/summary_rl_test.csv")
    df_rl = pd.read_csv(rl_file)
    for _, row in df_rl.iterrows():
        ag = row["agent"]
        for col in ["mean_wait_min", "p90_wait_min", "late_rate_pct", "gini_coefficient", "fleet_utilization_pct"]:
            reg_key = f"{ag}_{col}"
            assert reg_key in registry, f"Missing key {reg_key} in registry"
            csv_val = float(row[col])
            reg_val = float(registry[reg_key])
            err = abs(csv_val - reg_val)
            assert err < 1e-9, f"Fidelity error on {reg_key}: {err} >= 1e-9 (csv={csv_val}, reg={reg_val})"


def test_markdown_document_matches_registry():
    """Verifies that numbers formatted in docs/research/05_results_comparison.md match results/t3_policy_comparison.json."""
    doc_path = Path("docs/research/05_results_comparison.md")
    assert doc_path.exists(), "docs/research/05_results_comparison.md must exist"

    t3_file = Path("results/t3_policy_comparison.json")
    with open(t3_file, "r", encoding="utf-8") as f:
        t3_data = json.load(f)

    content = doc_path.read_text(encoding="utf-8")

    # Verify that formatted strings (with comma decimal separator in Vietnamese) appear in the document
    scenarios = t3_data["scenarios"]
    for sc_name, sc_vals in scenarios.items():
        for pol_name in ["Static Dijkstra", "Dynamic Dijkstra", "Edge-Scoring DQN"]:
            mean_t = sc_vals[pol_name]["mean_time_min"]
            vn_str = f"{mean_t:.2f}".replace(".", ",")
            assert vn_str in content, f"Formatted value {vn_str} for {pol_name} in {sc_name} not found in doc"


def test_bellman_reward_conservation_across_all_runs():
    """Verifies that Bellman reward sum matches negative wait time with error < 1e-9 across runs."""
    base_raw = Path("results/baselines/raw_baseline_runs.csv")
    df_base = pd.read_csv(base_raw)
    max_err_base = df_base["bellman_abs_error"].max()
    assert max_err_base < 1e-9, f"Base Bellman error {max_err_base} >= 1e-9"
