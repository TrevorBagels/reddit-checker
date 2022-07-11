#this program requires python 3.9+

from .prodict import Prodict
from . import utils
import os, requests

class Config(Prodict):
	client_id:	str	
	secret:		str
	username:	str
	password:	str
	
	def init(self):
		self.client_id = ""
		self.secret = ""
		self.username = ""
		self.password = ""
	


class Main:
	def __init__(self, conf="config.json"):
		self.config_file = conf

		#load config
		self.cfg:Config = Config.from_dict(utils.load_json(self.config_file))
		#save config file in case it doesn't exist or is incomplete
		utils.save_json(self.config_file, self.cfg.to_dict())

		self.get_token()
		pass

	def get_sensitive_config(self, key:str):
		"""Gets data from the config that might have been left blank. If blank, this will ask for input instead of reading data from the config.
		"""
		if self.cfg[key] not in ["", " ", None]:
			return self.cfg[key]
		else:
			return input(key + ": ")


	def get_token(self):
		#this isn't working, still trying to figure out why.
		auth = requests.auth.HTTPBasicAuth(self.cfg.client_id, self.cfg.secret)
		print(auth)
		#auth = (self.cfg.client_id, self.cfg.secret)
		login_data = {'grant_type': "password", "username": self.get_sensitive_config("username"), "password": self.get_sensitive_config("password")}
		r = requests.post("https://reddit.com/api/v1/access_token", auth=auth, data=login_data, headers={"User-Agent": "Python?"})
		print(r.content)
		print(r.json())


