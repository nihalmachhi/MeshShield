"""Optional two-layer GraphSAGE node classifier using PyTorch Geometric."""

from typing import Any


def fit_graph_sage(
    features: Any,
    edge_index: Any,
    labels: Any,
    train_mask: Any,
    epochs: int = 50,
    hidden_channels: int = 32,
    seed: int = 2025,
) -> Any:
    try:
        import torch
        from torch_geometric.nn import SAGEConv
    except ImportError as exc:
        raise RuntimeError("Install MeshShield with the 'graph' extra to use GraphSAGE") from exc
    if features.ndim != 2 or edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError("features must be a matrix and edge_index must have shape [2, edge_count]")
    if labels.shape[0] != features.shape[0] or train_mask.shape[0] != features.shape[0]:
        raise ValueError("features, labels, and train_mask must contain the same nodes")
    if epochs < 1 or hidden_channels < 1 or not train_mask.any():
        raise ValueError("epochs and hidden size must be positive and at least one node must train")
    torch.manual_seed(seed)

    class GraphSAGE(torch.nn.Module):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self.first = SAGEConv(features.shape[1], hidden_channels)
            self.second = SAGEConv(hidden_channels, 1)

        def forward(self, node_features: Any, edges: Any) -> Any:
            hidden = torch.relu(self.first(node_features, edges))
            return self.second(hidden, edges).squeeze(-1)

    model = GraphSAGE()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=0.001)
    loss_function = torch.nn.BCEWithLogitsLoss()
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(features, edge_index)
        loss = loss_function(logits[train_mask], labels.float()[train_mask])
        loss.backward()
        optimizer.step()
    model.eval()
    return model
