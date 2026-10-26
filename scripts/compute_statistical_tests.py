"""
Computes paired statistical tests (Wilcoxon signed-rank test with Holm-Bonferroni correction)
between Baselines and RL Agents on Frozen Test Seeds.
Saves results to results/training/paired_comparisons_rl.csv.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

def main():
    base_file = Path("results/baselines/raw_baseline_runs.csv")
    rl_file = Path("results/training/raw_rl_test_runs.csv")
    out_file = Path("results/training/paired_comparisons_rl.csv")

    df_base = pd.read_csv(base_file)
    df_rl = pd.read_csv(rl_file)

    # Filter standard test runs only (is_ood == False)
    df_base_test = df_base[df_base["is_ood"] == False].copy()
    df_rl_test = df_rl[df_rl["is_ood"] == False].copy()

    # Rename agent column to policy if needed
    if "agent" in df_rl_test.columns:
        df_rl_test["policy"] = df_rl_test["agent"]

    # Calculate seed-level averages for each policy
    base_pivot = df_base_test.pivot_table(index="seed", columns="policy", values="mean_wait_min")
    rl_pivot = df_rl_test.pivot_table(index="seed", columns="policy", values="mean_wait_min")

    combined = pd.concat([base_pivot, rl_pivot], axis=1)
    print("Combined Pivot Table (Mean Wait min across 5 test seeds):")
    print(combined)

    # Reference policy: Immediate dispatch (best online baseline)
    ref = "Immediate"
    comparisons = []
    
    other_policies = [c for c in combined.columns if c != ref]
    raw_p_values = []
    comp_records = []

    for pol in other_policies:
        diff = combined[pol].to_numpy() - combined[ref].to_numpy()
        mean_diff = float(np.mean(diff))
        pct_diff = (mean_diff / float(np.mean(combined[ref]))) * 100.0
        
        # Wilcoxon signed rank test
        # With n=5 seeds, use exact or zero_method
        try:
            res = stats.wilcoxon(combined[pol], combined[ref], alternative="two-sided")
            p_val = float(res.pvalue)
            stat = float(res.statistic)
        except Exception:
            p_val = 1.0
            stat = 0.0

        comp_records.append({
            "comparison": f"{pol} vs {ref}",
            "policy_a": pol,
            "policy_b": ref,
            "mean_a_min": float(np.mean(combined[pol])),
            "mean_b_min": float(np.mean(combined[ref])),
            "diff_min": mean_diff,
            "diff_pct": pct_diff,
            "wilcoxon_stat": stat,
            "raw_p_value": p_val,
        })
        raw_p_values.append(p_val)

    # Holm-Bonferroni correction
    # Sort by p-value
    m = len(raw_p_values)
    sorted_indices = np.argsort(raw_p_values)
    sorted_p = np.array(raw_p_values)[sorted_indices]
    
    adjusted_p = np.zeros(m)
    for i in range(m):
        rank = i + 1
        adj = sorted_p[i] * (m - rank + 1)
        adjusted_p[i] = min(adj, 1.0)
    
    # Enforce monotonicity: p_adj[i] >= p_adj[i-1]
    for i in range(1, m):
        adjusted_p[i] = max(adjusted_p[i], adjusted_p[i-1])

    for orig_idx, adj_p in zip(sorted_indices, adjusted_p):
        comp_records[orig_idx]["p_holm"] = float(adj_p)
        comp_records[orig_idx]["significant_005"] = bool(adj_p < 0.05)

    df_out = pd.DataFrame(comp_records)
    df_out.to_csv(out_file, index=False)
    print(f"\nSaved paired statistical tests to {out_file}:")
    print(df_out[["comparison", "diff_min", "diff_pct", "raw_p_value", "p_holm", "significant_005"]])

if __name__ == "__main__":
    main()
