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
	ratelimit_wait:	float #how long to pause for if we get ratelimited

	def init(self):
		self.sr_list =	"Altcannabinoids CannabisExtracts Cracksmokers Dabs Drugs DPH DXM Stims Trees Unclebens Weed"
		self.max_results = 150
		self.request_delay = .5
		self.ratelimit_wait = 2
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
	username:		str
	subreddit:		str
	total_posts:			int
	total_posts_exceeds:	bool #if number of posts is greater than max_results, which means that we weren't able to get an accurate summary of the results
	total_comments:			int
	total_comments_exceeds:	bool
	result_str:				str
	def init(self):
		self.total_posts_exceeds = False
		self.total_comments_exceeds = False
