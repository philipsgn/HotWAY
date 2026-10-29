"""
Automated Weight Ingestion & Re-Evaluation Script (HotWAY Phase 2).
Usage:
    python scripts/ingest_kaggle_weights.py --weights-path /path/to/downloaded_attention_tsp50_hcmc.pt
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

import torch

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")


def ingest_weights(weights_path: str = "results/attention_tsp50_hcmc.pt"):
    target_dest = Path("results/attention_tsp50_hcmc.pt")
    src = Path(weights_path)

    if not src.exists():
        print(f"Error: Weights file does not exist at '{src}'.")
        print("Please upload the file downloaded from Kaggle into 'results/attention_tsp50_hcmc.pt'")
        sys.exit(1)

    print("=" * 70)
    print("HOTWAY KAGGLE WEIGHT INGESTION & RE-EVALUATION PIPELINE")
    print("=" * 70)
    print(f"Checking candidate weights at: {src}")

    # Inspect state dict
    try:
        sd = torch.load(src, map_location="cpu", weights_only=True)
    except Exception as e:
        print(f"Failed to load checkpoint via torch.load: {e}")
        sys.exit(1)

    total_params = sum(p.numel() for p in sd.values())
    embed_dim = sd.get("encoder.init_embed.weight", sd.get("init_embed.weight")).shape[0] if "encoder.init_embed.weight" in sd or "init_embed.weight" in sd else "unknown"
    n_layers = len([k for k in sd.keys() if k.startswith("encoder.layers.") and k.endswith(".norm1.weight")])

    print(f"Total Model Parameters: {total_params:,}")
    print(f"Embedding Dimension: {embed_dim}")
    print(f"Transformer Encoder Layers: {n_layers}")

    if src.resolve() != target_dest.resolve():
        shutil.copy2(src, target_dest)
        print(f"Copied weights to target destination: {target_dest}")
    else:
        print(f"Weights already located at: {target_dest}")

    file_size_mb = os.path.getsize(target_dest) / (1024 * 1024)
    print(f"Checkpoint File Size: {file_size_mb:.2f} MB")

    print("\nRunning full 100 POI Multi-Model Benchmark across Hanoi, Da Nang, HCMC...")
    py_exec = sys.executable
    ret = subprocess.run([py_exec, "evaluate_benchmark.py"], check=False)
    if ret.returncode != 0:
        print("Warning: evaluate_benchmark.py returned non-zero code!")

    # Sync to frontend
    fe_dir = Path("frontend/public/data")
    fe_dir.mkdir(parents=True, exist_ok=True)
    for fname in ["benchmark_summary_table.csv", "benchmark_multi_model_results.json"]:
        src_f = Path("results") / fname
        if src_f.exists():
            shutil.copy2(src_f, fe_dir / fname)
            print(f"Synced {fname} to frontend/public/data/")

    print("\n" + "=" * 70)
    print("WEIGHT INGESTION & BENCHMARK COMPLETE!")
    print("All frontend assets are synchronized.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Kaggle GPU weights into HotWAY")
    parser.add_argument("--weights-path", type=str, default="results/attention_tsp50_hcmc.pt", help="Path to checkpoint .pt")
    args = parser.parse_args()
    ingest_weights(args.weights_path)

