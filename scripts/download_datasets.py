"""Download licensed research datasets directly through Kaggle's own CLI."""

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("paysim", "ieee-cis"))
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    kaggle = shutil.which("kaggle")
    if kaggle is None:
        parser.error("Kaggle CLI is required; install it and configure credentials locally")
    if args.dataset == "paysim":
        destination = args.root / "paysim"
        command = [
            kaggle,
            "datasets",
            "download",
            "-d",
            "ealaxi/paysim1",
            "-p",
            str(destination),
            "--unzip",
        ]
    else:
        destination = args.root / "ieee-cis"
        command = [
            kaggle,
            "competitions",
            "download",
            "-c",
            "ieee-fraud-detection",
            "-p",
            str(destination),
            "--unzip",
        ]
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True)
    print(f"Downloaded {args.dataset} files into {destination}; these files are ignored by Git.")


if __name__ == "__main__":
    main()
