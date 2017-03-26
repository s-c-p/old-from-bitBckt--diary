import os
import json
from contextlib import contextmanager

import utils

op = os.path


@contextmanager
def configReader(absFilePath):
	with open(absFilePath, mode="rt") as fp:
		config = json.load(fp)
	yield config
	with open(absFilePath, mode="wt") as fp:
		json.dump(config, fp)
	return


class ConfigFile():
	"""	following info is stored
		- last commit id
		- list of un-encrypted files (All files look securely encrypted)
	TODO: how to ensure single instance
	"""

	def __init__(self, configFile, targetDir):
		self.configFile = configFile
		self.targetDir = targetDir
		return

	def getPasswordHash(self):
		with configReader(self.configFile) as config:
			return config["password"]
	
	def getFileTemplate(self):
		with configReader(self.configFile) as config:
			return config["template"]                     # TODO: #future; can also refer to a file(think mustache.js), in which case do a quick shutil.copy2 into mydir cuz external world isn't reliable
	
	def getLastCommit(self):
		with configReader(self.configFile) as config:
			return config["last_commit"]
	
	def getUnEncList(self):
		with configReader(self.configFile) as config:
			return config["unsecure_files"].values()

	def setUnEncList(self, newList):					# for working with deep_scan of main file
		hashes = [utils.calcHash(_) for _ in newList]
		newDict = dict(zip(hashes, newList))
		with configReader(self.configFile) as config:
			config["unsecure_files"] = newDict
		return

	def getFileHash(self, absFilePath):
		with configReader(self.configFile) as config:
			dicn = config["unsecure_files"]
		for k, v in dicn.items():
			if absFilePath == v:
				hashVal = k
		return hashVal

	def recordFileHash(self, absFilePath):
		# DEVEL: ---- start ----
		# if utils.fileEncStatus(absFilePath) == "encrypted":
		# 	print("Why am I recording hash of an encrypted file")
		# 	emergencyShutdown(-1)
		# if absFilePath in config["unsecure_files"].values():
		# 	# this will never happen cuz decrypt can't be called twice on the
		# 	# same file
		# 	return False
		# DEVEL: ----  end  ----
		hashVal = utils.calcHash(absFilePath)
		with configReader(self.configFile) as config:
			config["unsecure_files"][hashVal] = absFilePath
		return

	def removeFileHash(self, absFilePath):
		key = self.getFileHash(absFilePath)
		with configReader(self.configFile) as config:
			popped = config["unsecure_files"].pop(key)
		assert popped == absFilePath
		return

# import subprocess
	# was a part of the crypto-wrapper function of diary.py
	# def recordCommitHead(self):
	# 	with utils.dirBongdi(self.targetDir):
	# 		x = subprocess.run("git log --max-count=1", stdout=subprocess.PIPE)
	# 	x = str(x.stdout, "CP437").splitlines()
	# 	_, __, ans = x[0].partition(" ")
	# 	with configReader(self.configFile) as config:
	# 		config["last_commit"] = ans
	# 	return



# def __del__(self):
# 	if op.isfile(CONFIG_FILE):
# 		fp = open(CONFIG_FILE, mode="wt")
# 	else:
# 		return
# 	with fp:
# 		json.dump(self.config, fp)
# 	return

# getPasswordHash = lambda self:  self.config["password"]
# getFileTemplate = lambda self:  self.config["template"]                     # TODO: #future; can also refer to a file(think mustache.js), in which case do a quick shutil.copy2 into mydir cuz external world isn't reliable
# getLastCommit = lambda self:    self.config["last_commit"]
# getUnEncList = lambda self:     self.config["unsecure_files"].values()

# def recordCommitHead(self):
# 	x = "git log --max-count=1"
# 	x = GitHandler(TARGET_DIR)._run(x, "record")
# 	x = str(x.stdout, "CP437").splitlines()
# 	_, __, ans = x[0].partition(" ")
# 	self.config["last_commit"] = ans
# 	return

# def recordFileHash(self, absFilePath):
# 	# DEVEL: ---- start ----
# 	if not utils.file_encrypted(absFilePath):
# 		print("Why am I recording hash of an encrypted file")
# 		emergencyShutdown(-1)
# 	if absFilePath in self.config["unsecure_files"].values():
# 		# this will never happen cuz decrypt can't be called twice on the
# 		# same file
# 		return False
# 	# DEVEL: ----  end  ----
# 	hashVal = calcHash(absFilePath)
# 	self.config["unsecure_files"][hashVal] = absFilePath
# 	return

# def getFileHash(self, absFilePath):
# 	for k, v in self.config["unsecure_files"].items():
# 		if absFilePath == v:
# 			hashVal = k
# 	return hashVal

# def removeFileHash(self, absFilePath):
# 	k = self.getFileHash(absFilePath)
# 	popped = self.config["unsecure_files"].pop(k)
# 	assert popped == absFilePath
# 	return