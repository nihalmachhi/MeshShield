"""Snapshot graph statistics for inspection, with a pure-Python fallback.

The per-row features in :mod:`meshshield.features.build` are incremental and
causal. This module is different: it answers "what does the graph look like
after the fact" for reports and the dashboard, so it must never be used to
build training rows.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from meshshield.core.domain import Transaction

Edge = tuple[str, str]


def account_device_edges(transactions: Iterable[Transaction]) -> set[Edge]:
    """Distinct account-device edges from any objects with those two attributes."""
    edges: set[Edge] = set()
    for tx in transactions:
        edges.add((tx.account_id, tx.device_id))
    return edges


def _adjacency(edges: Iterable[Edge]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for account, device in edges:
        adjacency[account].add(device)
        adjacency[device].add(account)
    return dict(adjacency)


def pagerank(
    edges: Iterable[Edge], damping: float = 0.85, iterations: int = 100, tolerance: float = 1e-12
) -> dict[str, float]:
    """Deterministic PageRank on an undirected bipartite account-device graph."""
    if not 0.0 < damping < 1.0:
        raise ValueError("damping must be in (0, 1)")
    if iterations < 1 or tolerance < 0:
        raise ValueError("iterations must be positive and tolerance non-negative")
    adjacency = _adjacency(edges)
    if not adjacency:
        return {}
    count = len(adjacency)
    ranks = {node: 1.0 / count for node in adjacency}
    for _ in range(iterations):
        updated = {
            node: (1.0 - damping) / count
            + damping * sum(ranks[peer] / len(adjacency[peer]) for peer in neighbours)
            for node, neighbours in adjacency.items()
        }
        delta = sum(abs(updated[node] - ranks[node]) for node in ranks)
        ranks = updated
        if delta < tolerance:
            break
    return dict(sorted(ranks.items()))


def community_labels(edges: Iterable[Edge]) -> tuple[dict[str, int], str]:
    """Community labels, using NetworkX when available and label propagation otherwise.

    Returns ``(labels, backend)`` so a report can state which implementation ran.
    """
    edge_list = sorted(set(edges))
    adjacency = _adjacency(edge_list)
    if not adjacency:
        return {}, "none"
    try:  # optional, never required for the core install
        import networkx as nx
    except ImportError:
        return _label_propagation(adjacency), "label-propagation"
    graph = nx.Graph()
    graph.add_edges_from(edge_list)
    communities = nx.community.greedy_modularity_communities(graph)
    labels: dict[str, int] = {}
    for index, members in enumerate(communities):
        for node in sorted(members):
            labels[node] = index
    return dict(sorted(labels.items())), "networkx-greedy-modularity"


def _label_propagation(adjacency: dict[str, set[str]]) -> dict[str, int]:
    labels = {node: index for index, node in enumerate(sorted(adjacency))}
    for _ in range(100):
        changed = False
        for node in sorted(adjacency):
            counts: dict[int, int] = defaultdict(int)
            for peer in sorted(adjacency[node]):
                counts[labels[peer]] += 1
            if not counts:
                continue
            best = max(counts.items(), key=lambda item: (item[1], -item[0]))[0]
            if best != labels[node]:
                labels[node] = best
                changed = True
        if not changed:
            break
    # Renumber to dense, deterministic ids.
    ordered = {label: index for index, label in enumerate(sorted(set(labels.values())))}
    return {node: ordered[label] for node, label in sorted(labels.items())}


def graph_summary(transactions: Iterable[Transaction], top_n: int = 10) -> dict[str, object]:
    """Top PageRank nodes and community sizes for a finished event stream."""
    edges = account_device_edges(transactions)
    ranks = pagerank(edges)
    labels, backend = community_labels(edges)
    sizes: dict[int, int] = defaultdict(int)
    for label in labels.values():
        sizes[label] += 1
    top = sorted(ranks.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    return {
        "edge_count": len(edges),
        "node_count": len(ranks),
        "pagerank_top": [{"node": node, "score": score} for node, score in top],
        "community_backend": backend,
        "community_count": len(sizes),
        "community_sizes": sorted(sizes.values(), reverse=True)[:top_n],
        "note": "Snapshot statistics for inspection only; not used as training features.",
    }
