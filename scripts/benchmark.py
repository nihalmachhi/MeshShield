"""Run and record a measured local synthetic generate/train benchmark."""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from meshshield.core.pipeline import generate_dataset, train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1600)
    parser.add_argument("--seed", type=int, default=2025)
    args = parser.parse_args()
    started = perf_counter()
    dataset = generate_dataset(args.count, args.seed)
    metrics = train_and_evaluate()
    elapsed_seconds = perf_counter() - started
    report = {
        "dataset": dataset["dataset_name"],
        "seed": args.seed,
        "rows": args.count,
        "elapsed_seconds": round(elapsed_seconds, 4),
        "rows_per_second": round(args.count / elapsed_seconds, 2),
        "holdout_metrics": metrics["graph_model_calibrated"],
        "note": (
            "One local synthetic run; timings depend on the machine "
            "and are not a production benchmark."
        ),
    }
    output = Path("output/benchmarks")
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / f"meshshield-{args.seed}-{args.count}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), **report}, indent=2))


if __name__ == "__main__":
    main()
