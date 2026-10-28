"""Model Exporter Utility for Kool et al. Attention Model.
Exports PyTorch weights (.pt) and ONNX (.onnx) runtime artifacts for production serving.
"""

from pathlib import Path
import torch
from .model import AttentionModel


def save_attention_model_checkpoint(
    model: AttentionModel,
    output_path: str = "results/attention_tsp50_hcmc.pt",
) -> Path:
    """Save PyTorch Attention Model weights for CPU inference."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(output_path))
    return output_path


def export_attention_model_to_onnx(
    model: AttentionModel,
    output_path: str = "results/attention_tsp50_hcmc.onnx",
    n_nodes: int = 20,
    input_dim: int = 3,
) -> Path:
    """Export trained PyTorch Attention Model to ONNX if onnxscript is available."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # First save the PyTorch checkpoint (.pt)
    pt_path = output_path.with_suffix(".pt")
    save_attention_model_checkpoint(model, pt_path)

    try:
        model.eval()
        dummy_input = torch.randn(1, n_nodes, input_dim, dtype=torch.float32)

        class OnnxTourWrapper(torch.nn.Module):
            def __init__(self, core_model):
                super().__init__()
                self.core_model = core_model

            def forward(self, x):
                tours, _ = self.core_model(x, decode_type="greedy")
                return tours

        wrapper = OnnxTourWrapper(model)
        torch.onnx.export(
            wrapper,
            dummy_input,
            str(output_path),
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["nodes"],
            output_names=["tours"],
            dynamic_axes={
                "nodes": {0: "batch_size", 1: "num_nodes"},
                "tours": {0: "batch_size", 1: "num_nodes"},
            },
        )
        return output_path
    except Exception as e:
        print(f"[Notice] ONNX export deferred ({e}); PyTorch weights saved at {pt_path}")
        return pt_path


def generate_reference_model(
    output_path: str = "results/attention_tsp50_hcmc.pt",
    seed: int = 2026,
) -> Path:
    """Instantiate a reproducible reference Attention Model and save weights."""
    torch.manual_seed(seed)
    model = AttentionModel(input_dim=3, embed_dim=64, n_heads=4, n_layers=2)
    return save_attention_model_checkpoint(model, output_path=output_path)


if __name__ == "__main__":
    path = generate_reference_model()
    print(f"Generated model checkpoint successfully at: {path}")
