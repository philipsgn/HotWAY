#!/usr/bin/env python3
"""HotWAY End-to-End Test Suite Runner.

Discovers and executes tests across 4 tiers:
- Tier 1: Feature Coverage & Contracts (tier1_features)
- Tier 2: Boundary & Extreme Limits (tier2_boundaries)
- Tier 3: Pairwise Combinations (tier3_pairwise)
- Tier 4: Real-World Workloads (tier4_workloads)

Usage:
    python tests/e2e/runner.py                   # Run all discovered tiers
    python tests/e2e/runner.py --tier 1          # Run Tier 1 only
    python tests/e2e/runner.py --tier 1 2        # Run Tiers 1 and 2
    python tests/e2e/runner.py --verbose         # Detailed per-test output
    python tests/e2e/runner.py --json            # Output structured JSON
    python tests/e2e/runner.py --output out.json # Save JSON report to path
"""

import argparse
import datetime
import json
import os
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional


TIER_DIRECTORY_MAP = {
    "1": "tier1_features",
    "2": "tier2_boundaries",
    "3": "tier3_pairwise",
    "4": "tier4_workloads",
}


class StructuredTestResult(unittest.TestResult):
    """Custom TestResult collecting detailed per-test structured records."""

    def __init__(self, tier_name: str, verbose: bool = False):
        super().__init__()
        self.tier_name = tier_name
        self.verbose = verbose
        self.records: List[Dict[str, Any]] = []
        self._test_start_time: float = 0.0

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self._test_start_time = time.perf_counter()
        if self.verbose:
            sys.stdout.write(f"  RUN  {test.id()} ... ")
            sys.stdout.flush()

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        duration = time.perf_counter() - self._test_start_time
        self.records.append({
            "test_id": test.id(),
            "tier": self.tier_name,
            "status": "PASS",
            "duration": round(duration, 4),
            "message": None,
        })
        if self.verbose:
            sys.stdout.write(f"PASS ({duration:.3f}s)\n")

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        super().addFailure(test, err)
        duration = time.perf_counter() - self._test_start_time
        message = self._exc_info_to_string(err, test)
        self.records.append({
            "test_id": test.id(),
            "tier": self.tier_name,
            "status": "FAIL",
            "duration": round(duration, 4),
            "message": message,
        })
        if self.verbose:
            sys.stdout.write(f"FAIL ({duration:.3f}s)\n")

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        super().addError(test, err)
        duration = time.perf_counter() - self._test_start_time
        message = self._exc_info_to_string(err, test)
        self.records.append({
            "test_id": test.id(),
            "tier": self.tier_name,
            "status": "ERROR",
            "duration": round(duration, 4),
            "message": message,
        })
        if self.verbose:
            sys.stdout.write(f"ERROR ({duration:.3f}s)\n")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        duration = time.perf_counter() - self._test_start_time
        self.records.append({
            "test_id": test.id(),
            "tier": self.tier_name,
            "status": "SKIP",
            "duration": round(duration, 4),
            "message": reason,
        })
        if self.verbose:
            sys.stdout.write(f"SKIP ({reason})\n")


def discover_and_run_tier(
    tier_name: str,
    tier_dir: Path,
    test_filter: Optional[str] = None,
    verbose: bool = False,
) -> tuple[StructuredTestResult, float]:
    """Discover and execute all tests in a single tier folder."""
    start_time = time.perf_counter()
    result = StructuredTestResult(tier_name=tier_name, verbose=verbose)

    if not tier_dir.is_dir():
        return result, 0.0

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(tier_dir),
        pattern="test_*.py",
        top_level_dir=str(tier_dir.parent.parent.parent),
    )

    # Optional test name filter
    if test_filter:
        filtered_suite = unittest.TestSuite()
        for test in _iter_tests(suite):
            if test_filter.lower() in test.id().lower():
                filtered_suite.addTest(test)
        suite = filtered_suite

    suite.run(result)
    tier_duration = time.perf_counter() - start_time
    return result, tier_duration


def _iter_tests(suite: Any):
    """Recursively iterate over test cases inside nested TestSuite."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def render_console_summary(report: Dict[str, Any]) -> None:
    """Renders a formatted console table summarizing the run."""
    summary = report["summary"]
    tiers = report["tiers"]

    print("\n" + "=" * 74)
    print("           HotWAY End-to-End Test Suite Execution Summary")
    print("=" * 74)
    print(f"Timestamp: {report['timestamp']}")
    print("-" * 74)
    print(f"{'Tier / Test Suite':<24} | {'Total':>6} | {'Pass':>6} | {'Fail':>6} | {'Err':>5} | {'Duration':>8}")
    print("-" * 74)

    for tier_name, tstats in tiers.items():
        total = tstats["total"]
        passed = tstats["passed"]
        failed = tstats["failed"]
        errors = tstats["errors"]
        dur = f"{tstats['duration']:.2f}s"
        print(f"{tier_name:<24} | {total:>6} | {passed:>6} | {failed:>6} | {errors:>5} | {dur:>8}")

    print("-" * 74)
    total_all = summary["total"]
    passed_all = summary["passed"]
    failed_all = summary["failed"]
    errors_all = summary["errors"]
    total_dur = f"{summary['duration_seconds']:.2f}s"
    print(f"{'TOTAL ALL TIERS':<24} | {total_all:>6} | {passed_all:>6} | {failed_all:>6} | {errors_all:>5} | {total_dur:>8}")
    print("=" * 74)

    # Print failures / errors details if any
    failed_records = [r for r in report["results"] if r["status"] in ("FAIL", "ERROR")]
    if failed_records:
        print("\nFAILURE / ERROR DETAILS:")
        print("-" * 74)
        for r in failed_records:
            print(f"[{r['status']}] {r['test_id']} ({r['tier']})")
            if r["message"]:
                print(r["message"].strip())
            print("-" * 74)

    if failed_all == 0 and errors_all == 0:
        print(f"\nOVERALL STATUS: ALL {total_all} TESTS PASSED (100% Pass Rate)\n")
    else:
        print(f"\nOVERALL STATUS: FAILED ({failed_all} failures, {errors_all} errors)\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="HotWAY E2E Test Suite Runner")
    parser.add_argument(
        "--tier",
        nargs="+",
        default=["all"],
        help="Tier numbers to run: '1', '2', '3', '4', or 'all' (default: all)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose execution details per test",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON report to standard output",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="File path to save JSON results (defaults to tests/e2e/reports/e2e_results.json)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Filter test cases by regex or substring pattern",
    )

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).resolve().parent
    project_root = base_dir.parent.parent

    # Add project root to sys.path so modules can be imported cleanly
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Resolve selected tiers
    selected_tiers = []
    if "all" in args.tier:
        selected_tiers = list(TIER_DIRECTORY_MAP.values())
    else:
        for t in args.tier:
            if t in TIER_DIRECTORY_MAP:
                selected_tiers.append(TIER_DIRECTORY_MAP[t])
            elif t in TIER_DIRECTORY_MAP.values():
                selected_tiers.append(t)
            else:
                print(f"Warning: Unknown tier identifier '{t}', skipping.", file=sys.stderr)

    if not selected_tiers:
        selected_tiers = list(TIER_DIRECTORY_MAP.values())

    all_records: List[Dict[str, Any]] = []
    tier_stats: Dict[str, Dict[str, Any]] = {}
    total_start = time.perf_counter()

    for tier_name in selected_tiers:
        tier_dir = base_dir / tier_name
        if not tier_dir.is_dir():
            continue

        if args.verbose:
            print(f"\n>>> Executing {tier_name} ({tier_dir})")

        result, dur = discover_and_run_tier(
            tier_name=tier_name,
            tier_dir=tier_dir,
            test_filter=args.filter,
            verbose=args.verbose,
        )

        all_records.extend(result.records)
        tier_stats[tier_name] = {
            "total": result.testsRun,
            "passed": len(result.records) - len(result.failures) - len(result.errors) - len(result.skipped),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "duration": round(dur, 4),
        }

    total_duration = time.perf_counter() - total_start

    total_tests = len(all_records)
    total_failed = sum(ts["failed"] for ts in tier_stats.values())
    total_errors = sum(ts["errors"] for ts in tier_stats.values())
    total_skipped = sum(ts["skipped"] for ts in tier_stats.values())
    total_passed = total_tests - total_failed - total_errors - total_skipped

    pass_rate = round((total_passed / total_tests * 100.0), 2) if total_tests > 0 else 0.0

    report = {
        "system": "HotWAY E2E Test Suite",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "total": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "errors": total_errors,
            "skipped": total_skipped,
            "pass_rate": pass_rate,
            "duration_seconds": round(total_duration, 4),
        },
        "tiers": tier_stats,
        "results": all_records,
    }

    # Write output JSON report
    report_path = Path(args.output) if args.output else (base_dir / "reports" / "e2e_results.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        render_console_summary(report)
        print(f"Structured JSON report saved to: {report_path}")

    # Return non-zero exit code if any failures or errors occurred
    return 0 if (total_failed == 0 and total_errors == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
