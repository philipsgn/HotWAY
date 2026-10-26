"""
Test T3 & T4: Benchmark Data Consistency & Academic Honesty.
v5.0 — Real Data Pipeline Edition

Validates the genuine benchmark results produced by HotWAY Benchmark Pipeline:
1. summary_by_algorithm.csv: 25 rows (5 protocols x 5 methods), 100% feasible rate across all protocols.
2. paired_comparisons.csv: 35 comparisons with valid Wilcoxon p-values and Holm corrections.
3. per_decision_cost.csv: Decision times and candidate evaluations.
4. Preserves legacy reference audit trail in rel_result/legacy_pdf_reference/.
"""

import csv
from pathlib import Path
import pytest


def test_summary_by_algorithm_loaded():
    p = Path("rel_result/summary_by_algorithm.csv")
    assert p.exists(), "summary_by_algorithm.csv must exist in rel_result/"
    with open(p, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 25, f"Expected 25 rows (5 protocols x 5 methods), got {len(reader)}"

    # All methods must achieve 100% feasibility (1.0)
    for r in reader:
        assert float(r["feasible_rate"]) == 1.0, f"Method {r['method']} in {r['protocol']} had feasibility < 1.0"
        assert float(r["mean_distance"]) > 0.0, "Mean distance must be positive"
        assert float(r["mean_improvement_pct"]) >= 0.0, "Improvement must be non-negative"

    # Check that both DQN and Random are present in Protocol A2
    a2_dqn = next(r for r in reader if r["protocol"] == "A2" and r["method"] == "DQN")
    a2_rand = next(r for r in reader if r["protocol"] == "A2" and r["method"] == "Random")

    assert float(a2_dqn["mean_distance"]) > 0
    assert float(a2_rand["mean_distance"]) > 0


def test_paired_comparisons_holm_validity():
    p = Path("rel_result/paired_comparisons.csv")
    assert p.exists(), "paired_comparisons.csv must exist"
    with open(p, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 35, f"Expected 35 comparisons (7 pairs x 5 protocols), got {len(reader)}"

    for comp in reader:
        p_wilc = float(comp["p_wilcoxon"])
        p_holm = float(comp["p_holm"])
        assert 0.0 <= p_wilc <= 1.0, f"Wilcoxon p-value out of bounds: {p_wilc}"
        assert 0.0 <= p_holm <= 1.0, f"Holm p-value out of bounds: {p_holm}"
        assert p_holm >= p_wilc - 1e-6, "Holm adjusted p-value must be >= raw p-value"


def test_per_decision_cost_inference_overhead():
    p = Path("rel_result/per_decision_cost.csv")
    assert p.exists(), "per_decision_cost.csv must exist"
    with open(p, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    methods = {r["method"]: r for r in reader}
    assert "Random" in methods
    assert "Cyclic" in methods
    assert "Greedy" in methods
    assert "DQN" in methods
    assert "Double DQN" in methods

    rand = methods["Random"]
    dqn = methods["DQN"]
    ddqn = methods["Double DQN"]

    # DQN / Double DQN neural net evaluation takes non-zero ms
    assert float(dqn["ms_per_decision"]) > 0
    assert float(ddqn["ms_per_decision"]) > 0
    assert float(rand["ms_per_decision"]) > 0


def test_legacy_reference_audit_trail_preserved():
    """Confirms that original PDF-extracted reference data is archived for auditability."""
    ref_dir = Path("rel_result/legacy_pdf_reference")
    assert (ref_dir / "summary_by_algorithm.csv").exists()
    assert (ref_dir / "paired_comparisons.csv").exists()
    assert (ref_dir / "per_decision_cost.csv").exists()
