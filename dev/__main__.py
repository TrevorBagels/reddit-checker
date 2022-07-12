
from . import main
import argparse
from . import utils

if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("--config", "-c", default="config.json", help="config file to use.")
	ap.add_argument("--user", "-u", help="username to analyze.")
	ap.add_argument("--search_preset", "-s", help="search preset to use from search_presets.json. not yet implemented.")
	args = ap.parse_args()

	m = main.Main(conf=args.config)

	def print_result(x:main.Result):
		s = " - /r/" + x.subreddit
		s += str( x.total_comments + x.total_posts )
		if x.total_comments_exceeds or x.total_posts_exceeds: s += "+"
		s += utils.pluralize("match", x.total_comments + x.total_posts, "matches", include_value=False)
		s += "\n\t" + utils.pluralize(str(x.total_posts), int(x.total_posts_exceeds) + 1, str(x.total_posts) + "+", include_value=False) + utils.pluralize("post", x.total_posts, "posts", include_value=False)
		s += "\n\t" + utils.pluralize(str(x.total_comments), int(x.total_comments_exceeds) + 1, str(x.total_comments) + "+", include_value=False) + utils.pluralize("comment", x.total_comments, "comments", include_value=False)
		print(s)

	data = m.get_user_subreddit_data(args.user, m.cfg.sr_list.split(" "), on_result=print_result)
	posts:list[main.Post] = data[0]
	comments:list[main.Comment] = data[1]
	results:list[main.Result] = data[2]