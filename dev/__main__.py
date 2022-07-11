
from . import main
import argparse


if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("--config", "-c", default="config.json", help="config file to use.")
	args = ap.parse_args()

	m = main.Main(conf=args.config)
	