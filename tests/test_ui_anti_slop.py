"""
Tests for UI Anti-AI-Slop and Hallmark The Floor compliance.
Verifies that:
1. No components in frontend/src/ use loose transition-all or transition: all.
2. No components use untamed heavy shadows (shadow-2xl) violating Swiss Monochromatic rules.
3. globals.css enforces text-wrap: balance and text-wrap: pretty for balanced Vietnamese typography.
4. DESIGN_SYSTEM.md and AGENTS.md document the anti-slop floor and preservation discipline.
"""

import os
from pathlib import Path
import pytest

FRONTEND_SRC = Path(__file__).resolve().parent.parent / "frontend" / "src"
ROOT_DIR = Path(__file__).resolve().parent.parent


def test_no_loose_transition_all():
    """Verify that zero files in frontend/src use transition-all or transition: all."""
    violations = []
    for root, _, files in os.walk(FRONTEND_SRC):
        for file in files:
            if file.endswith((".tsx", ".ts", ".jsx", ".js", ".css")):
                file_path = Path(root) / file
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    # Ignore commented lines if any
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*"):
                        continue
                    if "transition-all" in line or "transition: all" in line:
                        rel_path = file_path.relative_to(ROOT_DIR)
                        violations.append(f"{rel_path}:{line_idx} -> {line.strip()}")

    assert not violations, (
        f"Found {len(violations)} violations of Hallmark Mechanical Floor (banned transition: all):\n"
        + "\n".join(violations)
    )


def test_no_untamed_heavy_shadows():
    """Verify that zero files in frontend/src use shadow-2xl violating Monochromatic hairline rules."""
    violations = []
    for root, _, files in os.walk(FRONTEND_SRC):
        for file in files:
            if file.endswith((".tsx", ".ts", ".jsx", ".js", ".css")):
                file_path = Path(root) / file
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*"):
                        continue
                    if "shadow-2xl" in line:
                        rel_path = file_path.relative_to(ROOT_DIR)
                        violations.append(f"{rel_path}:{line_idx} -> {line.strip()}")

    assert not violations, (
        f"Found {len(violations)} violations of Swiss Monochromatic hairline rules (banned shadow-2xl):\n"
        + "\n".join(violations)
    )


def test_globals_css_text_wrapping_rules():
    """Verify that globals.css includes text-wrap: balance and text-wrap: pretty."""
    globals_css = FRONTEND_SRC / "app" / "globals.css"
    assert globals_css.exists(), f"Missing globals.css at {globals_css}"
    content = globals_css.read_text(encoding="utf-8")

    assert "text-wrap: balance" in content, "Missing 'text-wrap: balance' in globals.css"
    assert "text-wrap: pretty" in content, "Missing 'text-wrap: pretty' in globals.css"
    assert ".transition-subtle" in content, "Missing '.transition-subtle' helper in globals.css"


def test_design_system_and_agents_floor_documented():
    """Verify that DESIGN_SYSTEM.md and AGENTS.md document The Floor."""
    ds_path = ROOT_DIR / "DESIGN_SYSTEM.md"
    assert ds_path.exists()
    ds_content = ds_path.read_text(encoding="utf-8")
    assert "Quy Chuẩn Sàn Chống AI-Slop (Hallmark" in ds_content
    assert "Mechanical Floor" in ds_content
    assert "Typographic Flow Floor" in ds_content
    assert "Preservation Floor" in ds_content

    agents_path = ROOT_DIR / "AGENTS.md"
    assert agents_path.exists()
    agents_content = agents_path.read_text(encoding="utf-8")
    assert "Kỷ Luật The Floor (Hallmark Anti-AI-Slop)" in agents_content

