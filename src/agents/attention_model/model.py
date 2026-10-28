"""Attention Model for Combinatorial Optimization (TSP).
Based on Kool et al. (ICLR 2019): 'Attention, Learn to Solve Routing Problems!'
Adapted for Time-Dependent Urban Traffic Routing (HCMC Motorbike Deliveries).
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadAttention(nn.Module):
    """Multi-Head Attention module for Graph Encoder and Decoder."""

    def __init__(self, n_heads: int = 8, input_dim: int = 128, embed_dim: int = 128):
        super().__init__()
        self.n_heads = n_heads
        self.input_dim = input_dim
        self.embed_dim = embed_dim
        self.head_dim = embed_dim // n_heads

        self.w_q = nn.Linear(input_dim, embed_dim, bias=False)
        self.w_k = nn.Linear(input_dim, embed_dim, bias=False)
        self.w_v = nn.Linear(input_dim, embed_dim, bias=False)
        self.w_out = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, q, k=None, v=None, mask=None):
        if k is None:
            k = q
        if v is None:
            v = q

        batch_size = q.size(0)
        q_len = q.size(1)
        k_len = k.size(1)

        # Linear projections & split into heads
        q_s = self.w_q(q).view(batch_size, q_len, self.n_heads, self.head_dim).transpose(1, 2)
        k_s = self.w_k(k).view(batch_size, k_len, self.n_heads, self.head_dim).transpose(1, 2)
        v_s = self.w_v(v).view(batch_size, k_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(q_s, k_s.transpose(-2, -1)) / math.sqrt(self.head_dim)

        if mask is not None:
            # Broadcast mask across heads: mask shape (batch, 1, 1, k_len) or (batch, 1, q_len, k_len)
            scores = scores.masked_fill(mask == 1, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        context = torch.matmul(attn_weights, v_s)

        # Concatenate heads & final projection
        context = context.transpose(1, 2).contiguous().view(batch_size, q_len, self.embed_dim)
        return self.w_out(context)


class EncoderLayer(nn.Module):
    """Single Transformer Encoder layer with LayerNorm and Feed-Forward Network."""

    def __init__(self, embed_dim: int = 128, n_heads: int = 8, ffn_dim: int = 512):
        super().__init__()
        self.mha = MultiHeadAttention(n_heads=n_heads, input_dim=embed_dim, embed_dim=embed_dim)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, ffn_dim),
            nn.ReLU(),
            nn.Linear(ffn_dim, embed_dim),
        )
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        h = self.norm1(x + self.mha(x))
        out = self.norm2(h + self.ffn(h))
        return out


class Encoder(nn.Module):
    """Graph Transformer Encoder: projects raw node features and extracts deep graph embeddings."""

    def __init__(self, input_dim: int = 3, embed_dim: int = 128, n_heads: int = 8, n_layers: int = 3):
        super().__init__()
        self.init_embed = nn.Linear(input_dim, embed_dim)
        self.layers = nn.ModuleList([
            EncoderLayer(embed_dim=embed_dim, n_heads=n_heads) for _ in range(n_layers)
        ])

    def forward(self, x):
        h = self.init_embed(x)
        for layer in self.layers:
            h = layer(h)
        return h


class Decoder(nn.Module):
    """Autoregressive Pointer Decoder with time context for dynamic urban TSP."""

    def __init__(self, embed_dim: int = 128, n_heads: int = 8):
        super().__init__()
        self.embed_dim = embed_dim
        self.n_heads = n_heads
        # Context consists of: [graph_mean (128), depot (128), last_visited (128), time_ratio (1)]
        self.context_proj = nn.Linear(embed_dim * 3 + 1, embed_dim)
        self.mha = MultiHeadAttention(n_heads=n_heads, input_dim=embed_dim, embed_dim=embed_dim)

        # Single-head pointer mechanism for compatibility score
        self.w_q_ptr = nn.Linear(embed_dim, embed_dim, bias=False)
        self.w_k_ptr = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, embeddings, mask, last_node_idx, depot_idx, time_ratio):
        """Compute action logits over unvisited nodes.
        
        Args:
            embeddings: (batch_size, n_nodes, embed_dim)
            mask: (batch_size, n_nodes) - 1 for visited, 0 for available
            last_node_idx: (batch_size,) - index of last visited node
            depot_idx: (batch_size,) - index of depot node (usually 0)
            time_ratio: (batch_size, 1) - normalized accumulated time elapsed
            
        Returns:
            logits: (batch_size, n_nodes)
        """
        batch_size, n_nodes, _ = embeddings.size()

        # 1. Graph mean embedding
        graph_embed = embeddings.mean(dim=1)  # (batch_size, embed_dim)

        # 2. Extract last visited and depot embeddings
        batch_indices = torch.arange(batch_size, device=embeddings.device)
        last_embed = embeddings[batch_indices, last_node_idx]  # (batch_size, embed_dim)
        depot_embed = embeddings[batch_indices, depot_idx]     # (batch_size, embed_dim)

        # 3. Concatenate into context vector
        context = torch.cat([graph_embed, depot_embed, last_embed, time_ratio], dim=-1)
        query = self.context_proj(context).unsqueeze(1)  # (batch_size, 1, embed_dim)

        # 4. Attention over unvisited node embeddings
        mask_mha = mask.unsqueeze(1).unsqueeze(2)  # (batch_size, 1, 1, n_nodes)
        query_mha = self.mha(query, embeddings, embeddings, mask=mask_mha)

        # 5. Pointer mechanism for final selection logits
        q_ptr = self.w_q_ptr(query_mha)  # (batch_size, 1, embed_dim)
        k_ptr = self.w_k_ptr(embeddings) # (batch_size, n_nodes, embed_dim)

        scores = torch.matmul(q_ptr, k_ptr.transpose(-2, -1)).squeeze(1) / math.sqrt(self.embed_dim)
        scores = 10.0 * torch.tanh(scores)  # Capping logits [-10, 10] for numerical stability

        logits = scores.masked_fill(mask == 1, -1e9)
        return logits


class AttentionModel(nn.Module):
    """End-to-End Neural Combinatorial Optimization Model for TSP."""

    def __init__(
        self,
        input_dim: int = 3,
        embed_dim: int = 128,
        n_heads: int = 8,
        n_layers: int = 3,
    ):
        super().__init__()
        self.encoder = Encoder(input_dim=input_dim, embed_dim=embed_dim, n_heads=n_heads, n_layers=n_layers)
        self.decoder = Decoder(embed_dim=embed_dim, n_heads=n_heads)

    def forward(self, nodes, decode_type: str = "greedy"):
        """Run full autoregressive tour decoding.
        
        Args:
            nodes: (batch_size, n_nodes, input_dim)
            decode_type: 'greedy' or 'sampling'
            
        Returns:
            tours: (batch_size, n_nodes)
            log_probs: (batch_size,) cumulative log probabilities
        """
        batch_size, n_nodes, _ = nodes.size()
        embeddings = self.encoder(nodes)

        visited = torch.zeros(batch_size, n_nodes, dtype=torch.uint8, device=nodes.device)
        tours = []
        log_probs = []

        # Start at depot (node 0)
        curr_node = torch.zeros(batch_size, dtype=torch.long, device=nodes.device)
        depot_idx = torch.zeros(batch_size, dtype=torch.long, device=nodes.device)
        visited[:, 0] = 1
        tours.append(curr_node)

        total_time_ratio = torch.zeros(batch_size, 1, device=nodes.device)

        for step in range(1, n_nodes):
            logits = self.decoder(embeddings, visited, curr_node, depot_idx, total_time_ratio)
            probs = F.softmax(logits, dim=-1)

            if decode_type == "greedy":
                next_node = torch.argmax(probs, dim=-1)
            else:
                next_node = torch.multinomial(probs, num_samples=1).squeeze(-1)

            step_log_prob = F.log_softmax(logits, dim=-1)
            selected_log_prob = step_log_prob.gather(1, next_node.unsqueeze(-1)).squeeze(-1)
            log_probs.append(selected_log_prob)

            batch_idx = torch.arange(batch_size, device=nodes.device)
            visited[batch_idx, next_node] = 1
            curr_node = next_node
            tours.append(curr_node)

            total_time_ratio = total_time_ratio + (1.0 / n_nodes)

        tours = torch.stack(tours, dim=1)  # (batch_size, n_nodes)
        total_log_prob = torch.stack(log_probs, dim=1).sum(dim=1) if log_probs else torch.zeros(batch_size, device=nodes.device)
        return tours, total_log_prob
