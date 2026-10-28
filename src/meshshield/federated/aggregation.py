"""Deterministic sample-weighted FedAvg aggregation for local experiments."""

import math


def federated_average(client_weights: list[list[float]], sample_counts: list[int]) -> list[float]:
    if not client_weights or len(client_weights) != len(sample_counts):
        raise ValueError("provide one positive sample count for each client update")
    width = len(client_weights[0])
    if width == 0 or any(len(weights) != width for weights in client_weights):
        raise ValueError("client updates must have the same non-zero width")
    if any(count <= 0 for count in sample_counts):
        raise ValueError("client sample counts must be positive")
    if any(not math.isfinite(value) for update in client_weights for value in update):
        raise ValueError("client updates must contain finite values")
    total = sum(sample_counts)
    return [
        sum(update[index] * count for update, count in zip(client_weights, sample_counts)) / total
        for index in range(width)
    ]
