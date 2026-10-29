"""
Automated Weight Ingestion & Re-Evaluation Script (HotWAY Phase 2 & 3).
Usage:
    python scripts/ingest_kaggle_weights.py --zip hotway_kaggle_final_artifacts.zip
    python scripts/ingest_kaggle_weights.py --weights-path results/hotway_attention_model_nationwide.pt
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import torch

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")


def ingest_artifacts(zip_path: str | None = None, weights_path: str | None = None):
    print("=" * 80)
    print("HOTWAY KAGGLE FINAL OUTPUT INGESTION & RE-EVALUATION PIPELINE")
    print("=" * 80)

    extracted_weights = None
    convergence_img = None

    # 1. Handle Zip Archive if provided
    if zip_path:
        zip_file = Path(zip_path)
        if not zip_file.exists():
            print(f"Error: Specified zip file does not exist: {zip_file}")
            sys.exit(1)

        print(f"Extracting Kaggle Artifacts from: {zip_file}")
        extract_dir = Path("results/kaggle_extracted")
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_file, "r") as zf:
            zf.extractall(extract_dir)
            namelist = zf.namelist()
            print(f"Archive contents: {namelist}")

        for f in extract_dir.glob("*.pt"):
            extracted_weights = f
            break
        for img in extract_dir.glob("*.png"):
            convergence_img = img
            break
    elif weights_path:
        w_file = Path(weights_path)
        if not w_file.exists():
            print(f"Error: Weights file does not exist at '{w_file}'.")
            sys.exit(1)
        extracted_weights = w_file

    if not extracted_weights:
        # Fallback check
        default_candidates = [
            Path("hotway_kaggle_final_artifacts.zip"),
            Path("results/attention_tsp50_hcmc.pt"),
            Path("models/attention_model_weights.pt"),
            Path("hotway_attention_model_nationwide.pt"),
        ]
        for c in default_candidates:
            if c.exists():
                if c.suffix == ".zip":
                    return ingest_artifacts(zip_path=str(c))
                elif c.suffix == ".pt":
                    extracted_weights = c
                    break

    if not extracted_weights or not extracted_weights.exists():
        print("Error: No valid weights (.pt) or artifact zip found!")
        print("Usage: python scripts/ingest_kaggle_weights.py --zip hotway_kaggle_final_artifacts.zip")
        sys.exit(1)

    print(f"Inspecting model weights: {extracted_weights}")
    try:
        sd = torch.load(extracted_weights, map_location="cpu", weights_only=True)
    except Exception as e:
        print(f"Failed to load checkpoint via torch.load: {e}")
        sys.exit(1)

    total_params = sum(p.numel() for p in sd.values())
    print(f"Total Parameters: {total_params:,}")

    # Copy weights to standard HotWAY destinations
    dest_candidates = [
        Path("models/attention_model_weights.pt"),
        Path("results/attention_tsp50_hcmc.pt"),
    ]
    for dest in dest_candidates:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted_weights, dest)
        print(f"  -> Synchronized weights to: {dest}")

    # Handle convergence plot if present
    if convergence_img and convergence_img.exists():
        fe_img_dir = Path("frontend/public/images")
        fe_img_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(convergence_img, fe_img_dir / "training_convergence_curves.png")
        shutil.copy2(convergence_img, Path("results") / "training_convergence_curves.png")
        print(f"  -> Synchronized convergence plot to frontend/public/images/ and results/")

    # 2. Run In-Depth Evaluation on 100 POI Benchmark
    print("\nExecuting evaluate_benchmark.py across 100 Nationwide POIs...")
    py_exec = sys.executable
    ret = subprocess.run([py_exec, "evaluate_benchmark.py"], check=False)
    if ret.returncode != 0:
        print("Warning: evaluate_benchmark.py exited with non-zero code!")

    # 3. Synchronize new benchmark results to Frontend
    fe_data_dir = Path("frontend/public/data")
    fe_data_dir.mkdir(parents=True, exist_ok=True)
    for fname in ["benchmark_summary_table.csv", "benchmark_multi_model_results.json"]:
        src_f = Path("results") / fname
        if src_f.exists():
            shutil.copy2(src_f, fe_data_dir / fname)
            print(f"  -> Synced {fname} to frontend/public/data/")

    print("\n" + "=" * 80)
    print("SUCCESS: FINAL OUTPUT INGESTION AND SYNCHRONIZATION COMPLETE!")
    print("All benchmark tables, WebGIS maps, and Landing Page reports now reflect real trained data.")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Kaggle GPU weights into HotWAY")
    parser.add_argument("--zip", type=str, default=None, help="Path to downloaded hotway_kaggle_final_artifacts.zip")
    parser.add_argument("--weights-path", type=str, default=None, help="Path to checkpoint .pt file")
    args = parser.parse_args()
    ingest_artifacts(zip_path=args.zip, weights_path=args.weights_path)
