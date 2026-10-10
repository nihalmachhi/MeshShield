"""Command-line entry points for reproducible local runs."""

import argparse
import json

from meshshield.config import DEFAULT_SEED, DEFAULT_TRANSACTION_COUNT
from meshshield.pipeline import generate_dataset, load_or_prepare, train_and_evaluate
from meshshield.simulator import process_delivery, simulate_delivery
from meshshield.domain import SyncEvent
from meshshield.config import EVENTS_FILE
from meshshield.storage import IdempotencyStore, read_jsonl
from meshshield.web import serve


def main():
    parser = argparse.ArgumentParser(prog="meshshield", description="Synthetic offline payment risk research simulator")
    commands = parser.add_subparsers(dest="command", required=True)
    generate_cmd = commands.add_parser("generate", help="Generate a reproducible synthetic dataset")
    generate_cmd.add_argument("--count", type=int, default=DEFAULT_TRANSACTION_COUNT)
    generate_cmd.add_argument("--seed", type=int, default=DEFAULT_SEED)
    commands.add_parser("train", help="Train and compare the baseline models")
    commands.add_parser("evaluate", help="Print the latest chronological holdout metrics")
    commands.add_parser("demo", help="Run generation, model comparison, and sync replay summary")
    serve_cmd = commands.add_parser("serve", help="Start the local review dashboard")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "generate":
        print(json.dumps(generate_dataset(args.count, args.seed), indent=2))
    elif args.command == "train":
        print(json.dumps(train_and_evaluate(), indent=2))
    elif args.command == "evaluate":
        _, metrics, _ = load_or_prepare()
        print(json.dumps(metrics, indent=2))
    elif args.command == "demo":
        card = generate_dataset()
        metrics = train_and_evaluate()
        events = [SyncEvent(**row) for row in read_jsonl(EVENTS_FILE)]
        # Each demo run starts with a fresh store so the same seed gives the
        # same delivery summary; `serve` demonstrates persistent local storage.
        store = IdempotencyStore(":memory:")
        sync = process_delivery(simulate_delivery(events), store)
        store.close()
        print(json.dumps({"dataset": card, "metrics": metrics, "sync_simulation": sync}, indent=2))
    elif args.command == "serve":
        serve(args.host, args.port)


if __name__ == "__main__":
    main()
