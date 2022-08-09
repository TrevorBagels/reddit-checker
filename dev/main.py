from flask import Flask, Response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin

from .prodict import Prodict

from . import utils
from . import core
import os, requests, time, urllib.parse, threading

HOST = "0.0.0.0"
PORT = "5001"
AUTO = False


class UserSubredditMemory(Prodict):
	posts:		list[core.Post]
	comments:	list[core.Comment]
	
	def init(self):
		self.posts = []
		self.comments = []

class UserMemory(Prodict):
	name:		str
	subreddits:	dict[str, UserSubredditMemory]
	
	def init(self):
		self.subreddits = {}


class Main:
	def __init__(self, conf="config.json"):
		self.config_file = conf
		#load config
		self.cfg:core.Config = core.Config.from_dict(utils.load_json(self.config_file))
		#save config file in case it doesn't exist or is incomplete
		utils.save_json(self.config_file, self.cfg.to_dict())
		self.users:dict[str, UserMemory] = {} #each user has ["posts"] and ["comments"]

	


	def format_result_string(self, x:core.Result) -> str:
		s = "/r/" + x.subreddit + "<br>"
		s += str( x.total_comments + x.total_posts )
		if x.total_comments_exceeds or x.total_posts_exceeds: s += "+"
		s += " " + utils.pluralize("match", x.total_comments + x.total_posts, "matches", include_value=False)
		if x.total_comments + x.total_posts > 0:
			s += "<br>" + utils.pluralize(str(x.total_posts), int(x.total_posts_exceeds) + 1, str(x.total_posts) + "+", include_value=False) + " " + utils.pluralize("post", x.total_posts, "posts", include_value=False)
			s += "<br>" + utils.pluralize(str(x.total_comments), int(x.total_comments_exceeds) + 1, str(x.total_comments) + "+", include_value=False) + " " + utils.pluralize("comment", x.total_comments, "comments", include_value=False)
		return s

	def get_subreddit_user_data(self, username, subreddit) -> core.Result:

		result = None

		collect_data = True

		if username not in self.users:
			self.users[username] = UserMemory(name=username)
		if subreddit not in self.users[username].subreddits:
			self.users[username].subreddits[subreddit] = UserSubredditMemory()
		else:
			collect_data = False #we already ran a scan on this subreddit

		while collect_data == True: #break this loop if we don't get ratelimited
			params = {"author": username, "subreddit": subreddit, "size": self.cfg.max_results}
			r_submissions = requests.get("https://api.pushshift.io/reddit/search/submission/?" + urllib.parse.urlencode(params))
			time.sleep(self.cfg.request_delay)
			r_comments = requests.get("https://api.pushshift.io/reddit/search/comment/?" + urllib.parse.urlencode(params))
			time.sleep(self.cfg.request_delay)

			if r_submissions.status_code == 429 or r_comments.status_code == 429:
					print("ratelimited!")
					time.sleep(self.cfg.ratelimit_wait)
					continue
			elif r_submissions.status_code != 200 or r_comments.status_code != 200: #in case of error
				print("Something went wrong... (get user subreddit data requests)")
				print(r_submissions.status_code, r_comments.status_code)
				#print(r_submissions.url, r_submissions.status_code, "\n- - -\n", r_comments.url, r_comments.status_code, "\n- - -\n", r_submissions.content, "\n\n", r_comments.content)
				break
			else: #break after this
				sr = self.users[username].subreddits[subreddit]
				for x in r_submissions.json()["data"]: sr.posts.append(core.Post.from_dict(x))
				for x in r_comments.json()["data"]: sr.comments.append(core.Comment.from_dict(x))
				break
		
		sr = self.users[username].subreddits[subreddit]
		#create result
		r = core.Result(subreddit = subreddit, total_posts = len(sr.posts), total_comments = len(sr.comments) )
		#determine if there are more posts or comments than we were able to scan.
		if r.total_posts >= self.cfg.max_results: r.total_posts_exceeds = True
		if r.total_comments >= self.cfg.max_results: r.total_comments_exceeds = True
		result = r
		
		#do some text formatting so we don't have to do it in JS
		result.result_str = self.format_result_string(result)

		return result
		


class SubredditList(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app
	
	def get(self):
		#! ADD AUTHORIZATION
		return self.main.cfg.sr_list.split(" ")


class SubredditUserData(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app
	
	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		parser.add_argument("subreddit", type=str, required=True)
		args = parser.parse_args()
		r = self.main.get_subreddit_user_data(args.username, args.subreddit)
		return r




class FlaskAPI:
	def __init__(self, main):
		self.main = main
		self.app = Flask(__name__)
		self.app.config["SECRET_KEY"] = "yes"

		api = Api(self.app)
		cors = CORS(self.app)
		self.app.config["CORS_HEADERS"] = "Content-Type"
		api.add_resource(SubredditList, "/subredditlist", resource_class_kwargs={'main': self.main, 'app': self})
		api.add_resource(SubredditUserData, "/subreddituserdata", resource_class_kwargs={'main': self.main, 'app': self})

		#start api
		kwargs = {"host": HOST, "port": PORT}
		if AUTO:
			kwargs = {}
		#threading.Thread(target=self.app.run, kwargs=kwargs).start()
		self.app.run(**kwargs)
