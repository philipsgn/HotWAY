"""
HotWAY CVRP Statistical Analysis Module v5.0
Performs rigorous statistical testing on CVRP benchmark results.

Methods:
1. Wilcoxon Signed-Rank Test: Non-parametric paired test comparing strategy costs across instances.
2. Holm-Bonferroni Correction: Controls Family-Wise Error Rate (FWER) across multiple pairwise hypotheses.
3. Bootstrap 95% Confidence Interval: Empirical distribution of mean improvements (B=2000 resamples).
4. Effect Size: Cohen's d (dz).

Exports:
- rel_result/statistical_tests.csv
- rel_result/paired_comparisons.csv (matching Strategy Lab schema)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("statistical_analysis")


def bootstrap_ci_diff(
    diff: np.ndarray,
    n_resamples: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap CI for mean difference."""
    rng = np.random.RandomState(seed)
    n = len(diff)
    if n == 0:
        return 0.0, 0.0, 0.0
    
    means = np.empty(n_resamples)
    for i in range(n_resamples):
        sample = rng.choice(diff, size=n, replace=True)
        means[i] = np.mean(sample)

    low = float(np.percentile(means, 100 * (alpha / 2.0)))
    high = float(np.percentile(means, 100 * (1 - alpha / 2.0)))
    return float(np.mean(diff)), round(low, 3), round(high, 3)


def cohen_dz(x: np.ndarray, y: np.ndarray) -> float:
    """Computes Cohen's dz effect size for paired samples."""
    diff = x - y
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return float(np.mean(diff) / std_diff)


def compute_paired_comparisons(
    df_raw: pd.DataFrame,
    protocol: str = "A2",
) -> pd.DataFrame:
    """
    Computes paired comparisons between key strategies for a given protocol:
    DQN vs Random, DQN vs Cyclic, DQN vs Greedy, Double DQN vs Random, etc.
    """
    df_p = df_raw[df_raw["protocol"] == protocol]
    if df_p.empty:
        return pd.DataFrame()

    # Pivot improvement_pct with index=instance_id, columns=strategy
    pivot = df_p.pivot(index="instance_id", columns="strategy", values="improvement_pct").dropna()

    comparison_pairs = [
        ("DQN", "Random"),
        ("DQN", "Cyclic"),
        ("DQN", "Greedy"),
        ("Double DQN", "Random"),
        ("Double DQN", "Cyclic"),
        ("Double DQN", "Greedy"),
        ("DQN", "Double DQN"),
    ]

    records = []
    p_values = []

    for strat_a, strat_b in comparison_pairs:
        if strat_a not in pivot.columns or strat_b not in pivot.columns:
            continue

        vals_a = pivot[strat_a].values
        vals_b = pivot[strat_b].values

        # Diff in improvement percentage points: A - B (positive means A is better)
        diff = vals_a - vals_b
        mean_diff = float(np.mean(diff))

        # Bootstrap CI
        _, ci_low, ci_high = bootstrap_ci_diff(diff)

        # Win / Tie / Loss
        w = int(np.sum(diff > 0.02))
        t = int(np.sum(np.abs(diff) <= 0.02))
        l = int(np.sum(diff < -0.02))
        w_t_l = f"{w}/{t}/{l}"

        # Cohen's dz
        dz = cohen_dz(vals_a, vals_b)

        # Wilcoxon test
        try:
            stat, p_val = stats.wilcoxon(vals_a, vals_b, alternative="two-sided")
        except Exception:
            p_val = 1.0

        p_values.append(p_val)
        records.append({
            "protocol": protocol,
            "comparison": f"{strat_a} − {strat_b}",
            "delta_impr_pp": round(mean_diff, 3),
            "ci_lower": ci_low,
            "ci_upper": ci_high,
            "w_t_l": w_t_l,
            "dz": round(dz, 2),
            "p_wilcoxon": round(p_val, 4),
            "raw_p": p_val,
        })

    df_comp = pd.DataFrame(records)
    if not df_comp.empty:
        # Holm-Bonferroni correction
        m = len(df_comp)
        sorted_indices = np.argsort(df_comp["raw_p"].values)
        adj_p = np.empty(m)

        cum_max = 0.0
        for rank, idx in enumerate(sorted_indices):
            k = m - rank
            p = df_comp.loc[idx, "raw_p"]
            corrected = min(1.0, p * k)
            corrected = max(corrected, cum_max) # Enforce monotonicity
            cum_max = corrected
            adj_p[idx] = corrected

        df_comp["p_holm"] = [round(p, 4) for p in adj_p]
        df_comp = df_comp.drop(columns=["raw_p"])

    return df_comp


def perform_full_statistical_suite(
    raw_csv_path: Path | str = "rel_result/raw_runs.csv",
    output_dir: Path | str = "rel_result",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Performs tests across all protocols and exports paired_comparisons.csv and statistical_tests.csv."""
    p_raw = Path(raw_csv_path)
    if not p_raw.exists():
        raise FileNotFoundError(f"Raw benchmark data not found at {p_raw}")

    df_raw = pd.read_csv(p_raw)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    protocols = df_raw["protocol"].unique()
    all_pairs = []

    for proto in protocols:
        df_proto = compute_paired_comparisons(df_raw, protocol=proto)
        if not df_proto.empty:
            all_pairs.append(df_proto)

    df_all_pairs = pd.concat(all_pairs, ignore_index=True) if all_pairs else pd.DataFrame()

    paired_csv = out / "paired_comparisons.csv"
    df_all_pairs.to_csv(paired_csv, index=False)
    logger.info(f"Exported paired comparisons: {paired_csv} ({len(df_all_pairs)} rows)")

    stat_csv = out / "statistical_tests.csv"
    df_all_pairs.to_csv(stat_csv, index=False)

    return df_all_pairs, df_all_pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CVRP Statistical Analysis")
    parser.add_argument("--raw", type=str, default="rel_result/raw_runs.csv")
    parser.add_argument("--out", type=str, default="rel_result")
    args = parser.parse_args()

    perform_full_statistical_suite(args.raw, args.out)
