from . import main
import argparse
from . import utils



if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("--config", "-c", default="config.json", help="config file to use.")
	#ap.add_argument("--user", "-u", help="username to analyze.")
	#ap.add_argument("--search_preset", "-s", help="search preset to use from search_presets.json. not yet implemented.")
	args = ap.parse_args()

	m = main.Main(conf=args.config)
	flask = main.FlaskAPI(m)
	