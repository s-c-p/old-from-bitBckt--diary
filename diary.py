# TODO: in production ? use git to move files, do a manual commit
# TODO: all instances of 'filePath' and 'filename' be checked

import os
import shutil
import getpass
import argparse
import subprocess

import utils
import diaryDateLib as ddl
from configfile import ConfigFile

op = os.path																	# easy short hand 
EXTN = ".txt"
REPO_NAME = "Entries"
SHOW_GIT_ERR = False


class GitError(Exception):
	def __init__(self, errMsg):
		self.errMsg = errMsg.replace("\n", "\n\t")
	def __str__(self):
		return "\n\n\t"+self.errMsg+"\n\n"


class GitHandler():
	"""	custom API wrapper around Git Distributed Version Control System """

	def __init__(self):
		self.insideRepo = utils.dirBongdi(REPO_NAME)
		return

	def _run(self, cmdString):
		ans = subprocess.run(cmdString
			, stdout=subprocess.DEVNULL
			, stderr=subprocess.PIPE)
		err = str(ans.stderr, "CP437")
		if err:
			if err.startswith("warning: LF will be replaced by CRLF"):
				pass
			else:
				raise utils.GitError("Git ran into an error while executing:\n{}\n\nThe error was:\n{}".format(cmdString, err))
		return

	def makeCommitCmd(self, action, date, commitMsg=None):
		""" prepares a string to be supplied when doing 'git commit'
		NOTE: date is date represention of the file and not the commit
		date
		"""
		cmd_struct = 'git commit -m "{kyaHua}: {kiskoHua}{aorKuch}"'
		if action == "add":
			what = "Added new entry for"
		elif action == "change":
			what = "Changes made in diary entry for"
		elif action == "no change":
			what = "No changes made in diary entry for"
		else:
			raise utils.BadProgrammerError("Unknown action recieved")
		commitDetails = "\n\n"+commitMsg if commitMsg else ""
		answer = cmd_struct.format(kyaHua=what
			, kiskoHua=date
			, aorKuch=commitDetails)
		return answer

	def vigilante(self):
		with self.insideRepo:
			subprocess.run("git push", stderr=subprocess.DEVNULL)
		return

	# NOTE: ideally, the path to file in add() and update() should be
	# relative to the repo but git is smart so no need to take extra pains;
	# plus, diaryDateLib.path_to_date() would be safer with abspath values

	def add(self, absFilePath, commitMsg=None):
		date = ddl.path_to_date(absFilePath)
		with self.insideRepo:
			self._run(  'git add "{}"'.format(absFilePath)  )
			self._run(self.makeCommitCmd("add", date, commitMsg))
		return

	def update(self, absFilePath, changesMade, commitMsg=None):
		date = ddl.path_to_date(absFilePath)
		changeState = "change" if changesMade else "no change"
		with self.insideRepo:
			self._run(  'git stage "{}"'.format(absFilePath)  )
			self._run(self.makeCommitCmd(changeState, date, commitMsg))
		return


def getPassword():
	""" gets password in plain text via getpass.getpass()
	verification is done by trying to decrypt a standard message stored
	in a file called test, see code of utils.setup_pwd() to understand
	"""
	def _getpass():
		trial = getpass.getpass("Enter Password: ")
		try:
			utils.crypto('d', "test.enc", "test", trial)
		except ValueError:
			password = None
		else:
			# in the extremely rare, almost impossible, case when wrong
			# password does generate text, albeit garbled, that survived
			# AES256 decryption algorithm, we check if the file contains
			# what it ought to contain by matching hash against the
			# known value
			if utils.calcHash("test") == utils.SHA1_OF_TEST_FILE:
				password = trial
				utils.crypto('e', "test", "test.enc", password)
			else:
				password = None
			os.remove("test")
		return password
	for _ in range(3):
		x = _getpass()
		if x:	return x
		else:	print("Incorrect password!\n")
	raise utils.UserCausedError("Too many wrong password attempts!")

def cryptoWrapper(srcFile, action, password=None):
	""" a safety wrapper around the raw utils.crypto function. Prevents
	successive over-encryption/decryption of files. And keeps record of
	changes in plain text version of file.
	"""
	# Every time a file is decrypted, its hash is recorded in configFile, when
	# time comes to encrypt that file, we pause and compare old (recorded) hash
	# and new hash of the file, if they don't match, means file's content has
	# changed
	# NOTE: checking hashes of encrypted file, to determine weather contents
	# in plain text have changed or not, will not do the job because salt will
	# produce a different looking encrypted copy even when underlying plain
	# text is the same. So, hash of plain text file has to be recorded
	if action not in ["encrypt", "decrypt"]:
		raise utils.BadProgrammerError("illegal value of action parameter: {}".format(action))
	status = utils.fileEncStatus(srcFile)
	overDo_enc = action == "encrypt" and status == "encrypted"
	overDo_dec = action == "decrypt" and status == "not-encrypted"
	if overDo_enc or overDo_dec:
		print("Can't {} already {} file".format(action, status))
		raise utils.UserCausedError("User attempted to over-encrypt/decrypt a file, this is not allowed")
	elif (action == "encrypt") and (status == "not-encrypted"):
		newHash = utils.calcHash(srcFile)
		oldHash = configFile.getFileHash(srcFile)                               # NOTE: error means hashVal wasn't found by getFileHash() i.e. file's insecure state wasn't recorded
		hasFileChanged = False if newHash == oldHash else True
	elif (action == "decrypt") and (status == "encrypted"):
		pass
	# ------------------------------------------------------------------------- start: encryption part
	if not password:
		password = getPassword()
	temp_file = srcFile + ".temp"
	utils.crypto(action[0], srcFile, temp_file, password)
	utils.shredFile(srcFile, delAftOverwrite=False)
	shutil.copy2(src=temp_file, dst=srcFile)
	utils.shredFile(temp_file)
	# ------------------------------------------------------------------------- end: encryption part
	# ------------------------------------------------------------------------- start: state changing side effects
	if action == "encrypt":
		configFile.removeFileHash(srcFile)
		GitHandler().update(srcFile, hasFileChanged)
		print("Entry for '%s' encrypted successfully." % ddl.path_to_date(srcFile))
	else:
		configFile.recordFileHash(srcFile)
		os.startfile(srcFile)
	try:	GitHandler().vigilante()
	except:	pass
	return

def scan(explicit=False):
	# TODO: getLastCommit
	if explicit:
		not_secure = utils.deep_scan(TARGET_DIR)
		configFile.setUnEncList(not_secure)
	else:
		not_secure = configFile.getUnEncList()
	if len(not_secure) == 0:
		print("All files look securely encrypted")
	else:
		print("\nFollowing entries are still un-encrypted:")
		for aFile in not_secure:
			print("\t" + ddl.path_to_date(aFile))
		print("\nEncrypt them now?")
		if utils.replyIsYes():
			password = getPassword()
			for aFile in not_secure:
				cryptoWrapper(aFile, "encrypt", password)
	return

def _coaxQualifiedDate():
	date = ddl.validateDate()
	if type(date) is tuple:
		qualifiedDate = "%s %s, %s" % date
		print("Do you mean: {}?".format(qualifiedDate))
		if utils.replyIsYes():
			return qualifiedDate
	return False

def makeEntry(today=False):
	if today:
		date = ddl.getSystemDate()
		print("\nAccording to system clock, today it's: {}.".format(date))
		qualifiedDate = date if utils.replyIsYes() else None
	else:
		qualifiedDate = _coaxQualifiedDate()
	if qualifiedDate:
		# _makeFile(date)
		print("Creating diary entry...")
		filePath = ddl.date_to_path(qualifiedDate) + EXTN
		filePath = op.join(TARGET_DIR, filePath)
		if op.isfile(filePath):
			print("!!! An entry for '{}' already exists, do you want to open it?".format(qualifiedDate))
			if not utils.replyIsYes():	return
		else:
			os.makedirs(op.dirname(filePath), exist_ok=True)
			TEMPLATE = configFile.getFileTemplate()
			with open(filePath, mode="wt", encoding="UTF-8") as fh:
				GitHandler().add(filePath)
				fh.write(TEMPLATE % qualifiedDate)
			configFile.recordFileHash(filePath)
		os.startfile(filePath)
	return

def interactiveDecrypt(qualifiedDate=None):
	try:
		filePath = ddl.date_to_path(qualifiedDate) + EXTN
	except TypeError:
		qualifiedDate = _coaxQualifiedDate()
		if qualifiedDate:
			interactiveDecrypt(qualifiedDate)
	else:
		absFilePath = op.join(TARGET_DIR, filePath)
		if op.isfile(absFilePath):
			cryptoWrapper(absFilePath, "decrypt")
		else:
			print("Diary entry for this date hasn't been created yet")
	return

def main():
	parser = argparse.ArgumentParser(description="Tools to write a personal diary with peace of mind (v 0.1).")
	parser.add_argument("-s", "--scan", action="store_true", help="Scan and report for un-encrypted files, if any [Default Action].")
	parser.add_argument("-d", "--decrypt", help="[interactive] Decrypt the file you specify.")
	parser.add_argument("-n", "--new", action="store_true", help="Create new diary entry for today.")
	parser.add_argument("-cd", "--custom-date", action="store_true", help="[interactive] Create new diary entry for a given date.")
	parser.add_argument("-ls", "--list", help="List all diary entries made till date.")
	choiceIs = parser.parse_args()
	if choiceIs.new:
		makeEntry(today=True)
	elif choiceIs.custom_date:
		makeEntry()
	elif choiceIs.decrypt:	# TODO: needs a lot of improvement
		# front CLIPer
		interactiveDecrypt()
		# if op.isfile(choiceIs.decrypt):
		# 	absFilePath = op.abspath(choiceIs.decrypt)
		# 	cryptoWrapper(absFilePath, "decrypt")
		# else:
		# 	print("Not a file")
	elif choiceIs.scan:
		scan(explicit=True)
	elif choiceIs.list:
		utils.listDiaryEntries(TARGET_DIR)
	else:
		scan()
	return









if not op.isdir("data"):
	os.mkdir("data")

with utils.dirBongdi("data"):
	MY_PATH = os.getcwd() # op.dirname(__file__)
	TARGET_DIR = op.join(MY_PATH, REPO_NAME)
	CONFIG_FILE = op.join(MY_PATH, "configuration.do.not.edit")
	if op.isfile(CONFIG_FILE):
		pass # so that configFile can be made global
	else:
		print("Configuration file not found! Are you trying to setup?")
		if utils.replyIsYes():
			utils.setup(TARGET_DIR, CONFIG_FILE)
		else:
			raise utils.UserCausedError("User refused to continue with setup")
			shutil.rmdir("data")
	configFile = ConfigFile(CONFIG_FILE, REPO_NAME)
	main()
