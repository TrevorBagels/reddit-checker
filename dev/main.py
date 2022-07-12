#this program requires python 3.9+


from .prodict import Prodict
from . import utils
import os, requests, time, urllib.parse

class Config(Prodict):
	#client_id:	str	
	#secret:		str
	#username:	str
	#password:	str
	sr_list:		str #seperated by spaces
	max_results:	int
	request_delay:	float
	def init(self):
		self.sr_list =	"Altcannabinoids CannabisExtracts Cracksmokers Dabs Drugs DPH DXM Stims Trees Unclebens Weed"
		self.max_results = 150
		self.request_delay = .5
		pass
	
class SearchPreset(Prodict):
	sr_list:	str #list of subreddits


class Comment(Prodict):
	archived:			bool
	author:				str
	author_fullname:	str
	body:				str
	body_sha1:			str
	collapsed:			bool
	collapsed_reason:	str
	comment_type:		str
	controversiality:	int
	id:					str
	is_submitter:		bool
	link_id:			str
	locked:				bool
	no_follow:			bool
	parent_id:			str
	permalink:			str
	retrieved_utc:		int
	score:				int
	subreddit:			str
	subreddit_id:		str
	subreddit_name_prefixed:	str
	subreddit_type:		str

class Post(Prodict):
	author:				str
	author_fullname:	str
	author_is_blocked:	bool
	can_mod_post:		bool
	created_utc:		int
	domain:				str
	full_link:			str
	id:					str
	is_crosspostable:	bool
	is_meta:			bool
	is_original_content:		bool
	is_reddit_media_domain:		bool
	is_robot_indexable:			bool
	parent_whitelist_status:	str
	is_self:			bool
	is_video:			bool
	link_flair_text:	str
	permalink:			str
	pinned:				bool
	post_hint:			str
	pwls:				int
	retrieved_on:		int
	score:				int
	selftext:			str
	send_replies:		bool
	spoiler:			bool
	stickied:			bool
	subreddit:			str
	subreddit_id:		str
	subreddit_subscribers:		int
	subreddit_type:		str
	suggested_sort:		str
	title:				str
	total_awards_received:	int
	upvote_ratio:		int
	url:				str
	whitelist_status:	str
	over_18:			bool
	num_comments:		int
	num_crossposts:		int
	locked:				bool

class Result(Prodict):
	subreddit:		str
	total_posts:			int
	total_posts_exceeds:	bool #if number of posts is greater than max_results, which means that we weren't able to get an accurate summary of the results
	total_comments:			int
	total_comments_exceeds:	bool
	def init(self):
		self.total_posts_exceeds = False
		self.total_comments_exceeds = False



class Main:
	def __init__(self, conf="config.json"):
		self.config_file = conf
		#load config
		self.cfg:Config = Config.from_dict(utils.load_json(self.config_file))
		#save config file in case it doesn't exist or is incomplete
		utils.save_json(self.config_file, self.cfg.to_dict())
		pass
	

	def get_user_subreddit_data(self, username:str, sr_list:list[str], max_results=150, on_result=None): #on_result is a function called after a result is found.
		max_results = self.cfg.max_results
		posts = []
		comments = []
		results = []
		#for this function, we only index posts and comments restricted to the subreddits provided. good for looking into a user that uses reddit every minute and posts to an overwhelming number of subreddits.
		for sr in sr_list:
			params = {"author": username, "subreddit": sr, "size": max_results}
			r_submissions = requests.get("https://api.pushshift.io/reddit/search/submission/?" + urllib.parse.urlencode(params))
			time.sleep(self.cfg.request_delay)
			r_comments = requests.get("https://api.pushshift.io/reddit/search/comment/?" + urllib.parse.urlencode(params))
			time.sleep(self.cfg.request_delay)
			if r_submissions.status_code == 429 or r_comments.status_code == 429:
				time.sleep(2)
				print("ratelimited!")
				sr_list.append(sr) #since we're basically skipping this subreddit, add it to the end of sr_list so we try again.
				continue
			elif r_submissions.status_code != 200 or r_comments.status_code != 200: #in case of error
				print("Something went wrong... (get user subreddit data requests)")
				print(r_submissions.url, r_submissions.status_code, "\n- - -\n", r_comments.url, r_comments.status_code, "\n- - -\n", r_submissions.content, "\n\n", r_comments.content)
			else:
				#add posts/comments (prodict versions) to posts and comments lists.
				for x in r_submissions.json()["data"]: posts.append(Post.from_dict(x))
				for x in r_comments.json()["data"]: comments.append(Comment.from_dict(x))
				#create result
				r = Result(subreddit = sr, total_posts = len(r_submissions.json()["data"]), total_comments = len(r_comments.json()["data"]) )
				#determine if there are more posts or comments than we were able to scan.
				if r.total_posts >= max_results: r.total_posts_exceeds = True
				if r.total_comments >= max_results: r.total_comments_exceeds = True
				#save result, print it with on_result()
				results.append(r)
				if on_result != None: on_result(r)

		return posts, comments, results
	

			



	def get_sensitive_config(self, key:str):
		"""Gets data from the config that might have been left blank. If blank, this will ask for input instead of reading data from the config.
		"""
		if self.cfg[key] not in ["", " ", None]:
			return self.cfg[key]
		else:
			return input(key + ": ")

	"""
	scratch this, gonna use pushshift instead.
	def get_token(self):
		#this isn't working, still trying to figure out why.
		auth = requests.auth.HTTPBasicAuth(self.cfg.client_id, self.cfg.secret)
		print(auth)
		#auth = (self.cfg.client_id, self.cfg.secret)
		login_data = {'grant_type': "client_credentials", "device_id": "a7f8dpbc8dghf9d8hsas8c"} #, "username": self.get_sensitive_config("username"), "password": self.get_sensitive_config("password")}
		r = requests.post("https://reddit.com/api/v1/access_token", auth=auth, data=login_data, headers={"User-Agent": "test/0.0.1"})
		print(r.url, r.headers)
		print(r.content)
		print(r.json())
	"""

