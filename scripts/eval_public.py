"""Evaluate MeshShield's pipeline on a permitted public fraud dataset.

The dataset is never downloaded here and no result is baked in. Point the script
at a PaySim or IEEE-CIS CSV that you obtained under its own licence:

    python scripts/eval_public.py --dataset paysim \\
        --input data/raw/PS_20174392719_1491204439457_log.csv

The public data has different labels and no offline sync, so the output says so
and must not be compared with the synthetic results.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from meshshield.data.public_datasets import load_ieee_cis, load_paysim  # noqa: E402
from meshshield.eval.public import evaluate_public  # noqa: E402
from meshshield.models.registry import MODEL_CATALOG  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("paysim", "ieee-cis"), required=True)
    parser.add_argument("--input", type=Path, required=True, help="transactions CSV")
    parser.add_argument("--identity", type=Path, help="IEEE-CIS identity CSV (optional)")
    parser.add_argument("--limit", type=int, default=200_000, help="maximum rows to read")
    parser.add_argument("--model", choices=tuple(MODEL_CATALOG), default="logistic")
    parser.add_argument("--output", type=Path, help="write the JSON result here")
    args = parser.parse_args()
    if args.limit < 100:
        parser.error("--limit must be at least 100")
    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")
    if args.dataset == "paysim":
        transactions = list(load_paysim(args.input, args.limit))
    else:
        transactions = list(load_ieee_cis(args.input, args.identity, args.limit))
    result = evaluate_public(transactions, model_name=args.model)
    result["dataset"]["source"] = args.input.name
    result["dataset"]["adapter"] = args.dataset
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
