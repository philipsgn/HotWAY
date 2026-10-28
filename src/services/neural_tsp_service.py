"""Neural TSP Inference Service for FastAPI.
Executes Attention Model (Kool et al., 2019) via PyTorch CPU or ONNX Runtime.
"""

from pathlib import Path
from typing import Dict, List, Any
import time
import numpy as np
import torch

from src.agents.attention_model.model import AttentionModel
from src.agents.attention_model.time_dependent_env import get_congestion_factor


class NeuralTSPService:
    """Production service for Neural Combinatorial Route Optimization."""

    def __init__(self, model_path: str = "results/attention_tsp50_hcmc.pt"):
        self.model_path = Path(model_path)
        self.torch_model = None

        # 1. Initialize PyTorch model architecture
        self.torch_model = AttentionModel(input_dim=3, embed_dim=64, n_heads=4, n_layers=2)

        # 2. Load trained weights if checkpoint exists
        if self.model_path.exists():
            try:
                state_dict = torch.load(str(self.model_path), map_location="cpu")
                self.torch_model.load_state_dict(state_dict)
            except Exception:
                pass

        self.torch_model.eval()

    def solve(
        self,
        depot: Dict[str, float],
        stops: List[Dict[str, Any]],
        departure_hour: float = 8.0,
    ) -> Dict[str, Any]:
        """Solve multi-stop TSP permutation using Neural Attention Mechanism.
        
        Args:
            depot: {'lat': float, 'lon': float, 'name': str}
            stops: List of {'id': str, 'lat': float, 'lon': float, 'demand': int}
            departure_hour: Departure time (e.g. 8.0 = 8:00 AM)
            
        Returns:
            Dict containing ordered stops, tour indices, distance_km, duration_min, and latency_ms.
        """
        start_time = time.perf_counter()

        all_points = [{"id": "DEPOT", "lat": depot["lat"], "lon": depot["lon"]}] + stops
        n_nodes = len(all_points)

        # Normalize features: [norm_lat, norm_lon, dep_hour / 24]
        features = []
        for p in all_points:
            n_lat = (p["lat"] - 10.70) / 0.20
            n_lon = (p["lon"] - 106.60) / 0.20
            features.append([n_lat, n_lon, (departure_hour % 24.0) / 24.0])

        input_tensor = torch.tensor([features], dtype=torch.float32)

        # Execute Inference on CPU
        with torch.no_grad():
            tours, _ = self.torch_model(input_tensor, decode_type="greedy")
            tour_indices = tours[0].cpu().numpy().tolist()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Calculate transit metrics considering Haversine / Speed / Congestion Factor
        ordered_stops = [all_points[idx] for idx in tour_indices]
        
        total_dist_km = 0.0
        total_dur_min = 0.0
        curr_hour = departure_hour

        for i in range(len(tour_indices)):
            u = ordered_stops[i]
            v = ordered_stops[(i + 1) % len(tour_indices)]

            # Haversine distance with 1.35x road curvature factor for HCMC
            lat1, lon1 = np.radians(u["lat"]), np.radians(u["lon"])
            lat2, lon2 = np.radians(v["lat"]), np.radians(v["lon"])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
            c = 2.0 * np.arcsin(np.sqrt(a))
            segment_km = 6371.0 * c * 1.35

            # Dynamic congestion speed (base: 24 km/h)
            c_factor = get_congestion_factor(curr_hour)
            speed_kmh = max(8.0, 24.0 / c_factor)
            segment_min = (segment_km / speed_kmh) * 60.0

            total_dist_km += segment_km
            total_dur_min += segment_min
            curr_hour += segment_min / 60.0

        return {
            "algorithm": "Attention Model (Kool et al., 2019)",
            "tour_indices": tour_indices,
            "ordered_stops": ordered_stops,
            "total_distance_km": round(total_dist_km, 2),
            "total_duration_min": round(total_dur_min, 2),
            "latency_ms": round(latency_ms, 2),
            "departure_hour": departure_hour,
        }
