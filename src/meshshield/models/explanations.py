"""Additive mean-background explanations for the linear logistic baseline."""

from meshshield.models.logistic import LogisticModel


def explain_logit(model: LogisticModel, values: list[float]) -> dict[str, object]:
    """Return exact additive logit contributions relative to training feature means."""
    if len(values) != len(model.feature_names):
        raise ValueError("feature row width must match the fitted model")
    contributions = {
        name: weight * (value - mean) / scale
        for name, value, mean, scale, weight in zip(
            model.feature_names, values, model.means, model.scales, model.weights
        )
    }
    return {
        "base_logit": model.bias,
        "contributions": contributions,
        "logit": model.bias + sum(contributions.values()),
        "assumption": "linear model with independent feature attribution around training means",
    }
