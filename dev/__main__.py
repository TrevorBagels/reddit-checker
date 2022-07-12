
from . import main
import argparse


if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("--config", "-c", default="config.json", help="config file to use.")
	ap.add_argument("--user", "-u", help="username to analyze.")
	ap.add_argument("--search_preset", "-s", help="search preset to use from search_presets.json. not yet implemented.")
	args = ap.parse_args()

	m = main.Main(conf=args.config)

	data = m.get_user_subreddit_data(args.user, m.cfg.sr_list.split(" "))
	posts:list[main.Post] = data[0]
	comments:list[main.Comment] = data[1]
	results:list[main.Result] = data[2]

	for x in results:
		pass