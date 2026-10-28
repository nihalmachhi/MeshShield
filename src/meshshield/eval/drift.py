"""Population stability diagnostics for numeric feature distributions."""

import math


def population_stability_index(
    reference: list[float], current: list[float], bins: int = 10
) -> float:
    if not reference or not current or bins < 2:
        raise ValueError("PSI needs non-empty samples and at least two bins")
    if any(not math.isfinite(value) for value in reference + current):
        raise ValueError("PSI inputs must be finite")
    sorted_reference = sorted(reference)
    edges = [
        sorted_reference[min(len(sorted_reference) - 1, int(index * len(sorted_reference) / bins))]
        for index in range(1, bins)
    ]
    reference_counts = [0] * bins
    current_counts = [0] * bins
    for value in reference:
        reference_counts[sum(value > edge for edge in edges)] += 1
    for value in current:
        current_counts[sum(value > edge for edge in edges)] += 1
    epsilon = 1e-6
    reference_total, current_total = len(reference), len(current)
    psi = 0.0
    for reference_count, current_count in zip(reference_counts, current_counts):
        reference_share = max(reference_count / reference_total, epsilon)
        current_share = max(current_count / current_total, epsilon)
        psi += (current_share - reference_share) * math.log(current_share / reference_share)
    return psi
