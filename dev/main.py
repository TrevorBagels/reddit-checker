import dotenv
from flask import Flask, Response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin

from .prodict import Prodict

from . import utils
from . import core
import os, requests, time, urllib.parse, threading, hashlib, json, os, random

from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer

from dotenv import load_dotenv

auth = HTTPBasicAuth()

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
		s = "<b>/r/" + x.subreddit + "</b><br><div>"
		s += str( x.total_comments + x.total_posts )
		if x.total_comments_exceeds or x.total_posts_exceeds: s += "+"
		s += " " + utils.pluralize("match", x.total_comments + x.total_posts, "matches", include_value=False)
		if x.total_comments + x.total_posts > 0:
			url = urllib.parse.quote(f"https://reddit.com/search/?q=author:{x.username} subreddit:{x.subreddit}") + "&type="
			url = f"https://reddit.com/search/?q=author%3A{x.username}%20subreddit%3A{x.subreddit}&type="

			s += "<br>" + f"<a target='_blank' href='{url}{'links'}'>" + utils.pluralize(str(x.total_posts), int(x.total_posts_exceeds) + 1, str(x.total_posts) + "+", include_value=False) + " " + utils.pluralize("post", x.total_posts, "posts", include_value=False) + "</a>"
			s += "<br>" + f"<a target='_blank' href='{url}{'comment'}'>" + utils.pluralize(str(x.total_comments), int(x.total_comments_exceeds) + 1, str(x.total_comments) + "+", include_value=False) + " " + utils.pluralize("comment", x.total_comments, "comments", include_value=False) + "</a>"
		s += "</div>"
		if x.total_comments + x.total_posts > 0: s = "<div class='redborder'>" + s + "</div>"


		else: s = "<div>" + s + "</div>"
		return s

	def get_subreddit_user_data(self, username, subreddit) -> core.Result:
		time.sleep(.25)
		result = None

		collect_data = True

		if username not in self.users:
			self.users[username] = UserMemory(name=username)
		if subreddit not in self.users[username].subreddits:
			self.users[username].subreddits[subreddit] = UserSubredditMemory()
		else:
			collect_data = False #we already ran a scan on this subreddit

		while collect_data == True: #break this loop if we don't get ratelimited
			try:
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
			except:
				time.sleep(3)
				print("something went wrong... trying again.", subreddit)
				continue
		
		sr = self.users[username].subreddits[subreddit]
		#create result
		r = core.Result(subreddit = subreddit, username = username, total_posts = len(sr.posts), total_comments = len(sr.comments) )
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
		if self.app.verify() == False:
			return "Unauthorized"
		return self.main.cfg.sr_list.split(" ")


class SubredditUserData(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app
	
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"

		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		parser.add_argument("subreddit", type=str, required=True)
		args = parser.parse_args()
		r = self.main.get_subreddit_user_data(args.username, args.subreddit)
		return r


class Authorized(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app
	
	def get(self):
		if self.app.verify() == False:
			return "Unauthorized"
		else:
			return "Authorized"

class SetPassword(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app
	
	def post(self):
		if self.app.verify() == False:
			return "Unauthorized"
		
		parser = reqparse.RequestParser()
		parser.add_argument('original', type=str, required=True)
		parser.add_argument('new', type=str, required=True)
		args = parser.parse_args()
		if self.app.get_pwd_hash(args.original) == os.environ.get("pass"):
			dotenv.set_key(".env", "pass", self.app.get_pwd_hash(args.new))
			return "<b style='color:lightgreen;'>Password set.</b>"
		else:
			return "<b style='color:lightred;'>Unauthorized or invallid password</b>"

class GenerateToken(Resource):
	def __init__(self, main:Main, app):
		self.main = main
		self.app = app

	def get(self): #gets a token
		parser = reqparse.RequestParser()
		parser.add_argument('password', required=True)
		args = parser.parse_args()
		password = args.password
		
		pwd_hash = self.app.get_pwd_hash(password)

		if os.environ.get("pass") == pwd_hash:
			s = TimedJSONWebSignatureSerializer(self.app.app.config["SECRET_KEY"], expires_in=60*60*24)
			token = s.dumps({}).decode()
			return token
		else:
			print("Unauthorized access attempt")
			return None


class FlaskAPI:
	def __init__(self, main):
		load_dotenv()
		self.main = main
		self.app = Flask(__name__)
		self.app.config["SECRET_KEY"] = "0789QV0O-KPL,H297384TRUIOBFUWhIASLC7TYVOUgsid"

		api = Api(self.app)
		cors = CORS(self.app)
		self.app.config["CORS_HEADERS"] = "Content-Type"
		api.add_resource(SubredditList, "/subredditlist", resource_class_kwargs={'main': self.main, 'app': self})
		api.add_resource(SubredditUserData, "/subreddituserdata", resource_class_kwargs={'main': self.main, 'app': self})
		
		api.add_resource(Authorized, "/checkauth", resource_class_kwargs={'main': self.main, 'app': self})
		api.add_resource(SetPassword, "/setpass", resource_class_kwargs={'main': self.main, 'app': self})
		api.add_resource(GenerateToken, "/gettoken", resource_class_kwargs={'main': self.main, 'app': self})

		if os.environ.get("pass") == None:
			pwd = self.get_pwd_hash("defaultpass")
			dotenv.set_key(".env", "pass", pwd)

		#start api
		kwargs = {"host": HOST, "port": PORT}
		if AUTO:
			kwargs = {}
		#threading.Thread(target=self.app.run, kwargs=kwargs).start()
		self.app.run(**kwargs)
	

	def get_pwd_hash(self, txt):
		salt = os.environ.get("salt")
		if salt == None:
			salt = random.randint(-99999999, 99999999)
			dotenv.set_key('.env', 'salt', str(salt))
		print(salt, txt)
		p = hashlib.pbkdf2_hmac('sha256', str(txt).encode(), str(salt).encode(), 110000).hex()
		print(p)
		return p

	def verify(self): #verify access token
		parser = reqparse.RequestParser()
		parser.add_argument('token', required=True)
		args = parser.parse_args()
		token = args.token
		s = TimedJSONWebSignatureSerializer(self.app.config["SECRET_KEY"])
		try:
			data = s.loads(token.encode())
		except SignatureExpired:
			return False #token is expired
		except BadSignature:
			return False #token never existed
		
		return True
