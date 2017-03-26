import gc
import os
import sys
import json
import shlex
import shutil
import hashlib
import calendar
import subprocess
from getpass import getpass
from contextlib import contextmanager

import diaryDateLib

TEST_FILE_DATA = "Written in UTF-8 using only ASCII characters."
SHA1_OF_TEST_FILE = "6f00feeb02084801fa80ecc14e26df19e4c78a17"


class CommandError(Exception):
	def __init__(self, cmnd, errMsg):
		self.cmnd = cmnd
		self.errMsg = errMsg.replace("\n", "\n\t")
	def __str__(self):
		return '\n !! "{}" gave the following error:\n\n\t{}\n'\
			.format(self.cmnd, self.errMsg)

class BadProgrammerError(Exception):
	def __init__(self, reason=""):
		self.reason = reason
	def __str__(self):
		ans = "Sucks! This should never have happened"
		if self.reason:
			ans+= "\n\nReason: {}".format(self.reason)
		return ans

class UserCausedError(BadProgrammerError):
	pass


@contextmanager
def dirBongdi(dirPath):
	init = os.getcwd()
	os.chdir(dirPath)
	yield
	os.chdir(init)


replyIsYes = lambda: input("[y]es or [N]o >>> ").lower().startswith("y")

def _runGitSetup(repoName):
	STEPS = [
		"git init",
		'git config --local user.name "%s"' % input("Enter your name: "),
		'git config --local user.email "%s"' % input("Enter your (valid) email: "),
		'git remote add gitBackup %s' % input("Enter URL to git server: ")
	]
# see the instructions given @ bitbucket
# https://github.com/diaryAccount/test_diary
# https://www.mailinator.com/inbox2.jsp?public_to=diaryaccount#/#public_maildirdiv
# https://stackoverflow.com/questions/13030714/git-fatal-the-current-branch-master-has-multiple-upstream-branches-refusing-t
# git remote -v
# git remote rm ...
# git config -l

	if os.path.isdir(repoName):
		print("%(repoName)s already exists, delete it \
		AFTER BACKING UP ANY NECESSARY DATA" % locals())
		os.startfile(".")
		return False
	os.mkdir(repoName)
	with dirBongdi(repoName) as _:
		for cmnd in STEPS:
			x = subprocess.run(
				shlex.split(cmnd),
				stderr=subprocess.PIPE
			)
			if len(x.stderr) > 0:
				print("Error encountered")
				input(str(x.stderr, "CP437"))
				return False
		with open("README.txt", mode="wt") as fh:
			fh.write("Files are encrypted, don't edit anything manually here")
		subprocess.run("git add README.txt", stdout=subprocess.DEVNULL)
		subprocess.run('git commit -m "First commit: installs warning file"', stdout=subprocess.DEVNULL)
	return True

def setup_git(repoName):
	while True:
		x = _runGitSetup(repoName)
		if x:	break
		input("Press enter to proceed")
	return True

def setup_template():
	def _check(f):
		if not os.path.isfile(f):		return False
		with open(f, mode="rt") as fp:	contents = fp.read()
		x = contents.count(r"%s")
		if x == 1:
			return contents
		return False
	print("!!! IMPORTANT - the template file must contain exactly 1 '%s' string holder (for date)")
	for _ in range(3):
		# print("\n\n\n\n")
		f = input("Enter path to template file: ")
		data = _check(f)
		if data:	break
		else:		print("_"*78)
	if not data:
		data = "%s\n-------------------------------\n\n"
		print("! Too many attempts, falling back to default template")
	return data

def crypto(action, srcFile, destFile, password):
	cmdStr = 'openssl enc -aes-256-cbc -{what} -a -in "{src}" -out "{dst}" -k "{key}"'
	ans = subprocess.run(
		shlex.split(
			cmdStr.format(
				what=action, src=srcFile, dst=destFile, key=password
		)), stderr=subprocess.PIPE)
	del password, cmdStr
	gc.collect()
	if ans.stderr:
		raise ValueError("OpenSSL's AES decrypt failed, possibly due to wrong password")
	return

def setup_pwd():
	print("\nFor security purposes, when you type the password it will not appear on screen\n")
	while True:
		x = getpass("Enter password for encryption: ")
		y = getpass("For confirmation, enter the same password again: ")
		if x or y:
			if x == y:	break
			else:		print("Passwords do not match", end="\n"+"_"*78+"\n")
		else:			print("Empty password not allowed", end="\n"+"_"*78+"\n")
	with open("test", mode="wt", encoding="UTF-8") as fp:
		fp.write(TEST_FILE_DATA)
	crypto('e', "test", "test.enc", x)
	os.remove("test")
	return

def calcHash(filePath, algo="sha1"):
	try:
		hasher = getattr(hashlib, algo)()
	except AttributeError:
		raise BadProgrammerError("hashing algorithm {}, is not supported".format(algo))
	with open(filePath, mode="rb") as fp:
		while True:
			block = fp.read(5 * 1024 * 1024)
			if len(block) == 0: break
			hasher.update(block)
	return hasher.hexdigest()

def fileEncStatus(filename):
	""" checks if a file is encrypted or not
	How? Well, all encrypted files (in context of this app) are base64
	encoded, and base64 will not have spaces - so if space is found then
	file is plain text, otherwise it is encrypted
	"""
	SPACE = " "
	try:
		fileHandle = open(filename, mode="rt")
	except:     #TODO: xxxDecodeError
		raise RuntimeError("! Problem accessing/reading this file: {}".format(filename))
	with fileHandle:
		lnum = 1	# not using enum in for loop because we will count line only if its not empty
		for aLine in fileHandle:
			if SPACE in aLine:
				return "not-encrypted"
			lnum+= 1 if aLine else 0
			if lnum > 100:	break
			# no hope of finding spaces any further
	return "encrypted"

def test():
	print("Start tests?")
	if replyIsYes():
		pass
	else:
		return

	input('\nsetup_pwd()')
	print(setup_pwd())
	input('\nsetup_template()')
	print(setup_template())
	input('\nsetup_git("FUCKSI")')
	print(setup_git("FUCKSI"))
	input('\nfileEncStatus("notes.txt")')
	print(fileEncStatus("notes.txt"))
	input('\ncalcHash("notes.txt")')
	print(calcHash("notes.txt"))
	input('\ncalcHash("notes.txt", "md5")')
	print(calcHash("notes.txt", "md5"))

	return

# if __name__ == '__main__':
# 	tes

def shredFile(absFilePath, delAftOverwrite=True):
	originalSize = os.stat(absFilePath).st_size
	with open(absFilePath, mode="wb") as fp:
		fp.write(os.urandom(originalSize))
		fp.write(os.urandom(originalSize))
		print("Shreading temp files")
		fp.seek(os.SEEK_SET);	fp.write(os.urandom(originalSize))
		fp.seek(os.SEEK_SET);	fp.write(os.urandom(originalSize))
	if delAftOverwrite:
		os.remove(absFilePath)
	return

def deep_scan(which_dir):
	def isFileValid(x):
		EXTN = ".txt"	# ugly, this const was declared in diary.py
		if os.path.isfile(x) and x.endswith(EXTN):
			return True
		return False
	print("Running deep scan . . .")
	VCS = ".git"
	temp = list()
	not_secure = list()
	for root, dirs, files in os.walk(which_dir):
		if VCS in dirs:
			dirs.remove(VCS)
		if root == which_dir and "README.txt" in files:
			files.remove("README.txt")
		temp+= [os.path.join(root, _) for _ in files]
	temp = [_ for _ in filter(isFileValid, temp)]								# why? # TODO: optimize this, some None are also coming
	for aFile in temp:
		if fileEncStatus(aFile) == "not-encrypted":
			not_secure.append(aFile)
	return not_secure

def setup(targetDir, configFilePath):
	config = dict()
	setup_pwd()
	config["template"] = setup_template()
	setup_git(targetDir)	# SHOuld it be REPO_NAME?
	config["last_commit"] = ""	# TODO: faulty
	config["unsecure_files"] = dict()
	with open(configFilePath, "wt") as fp:
		json.dump(config, fp)
	print("Setup successful")
	sys.exit(0)
	return

# """
# >>> calObj = c.TextCalendar(firstweekday=0)
# >>> calObj.formatmonth(2017, 3)
# '     March 2017\nMo Tu We Th Fr Sa Su\n       1  2  3  4  5\n 6  7  8  9 10 11 12\n13 14 15 16 17 18 19\n20 21 22 23 24 25 26\n27 28 29 30 31\n'
# >>> print(calObj.formatmonth(2017, 3))
#      March 2017
# Mo Tu We Th Fr Sa Su
#        1  2  3  4  5
#  6  7  8  9 10 11 12
# 13 14 15 16 17 18 19
# 20 21 22 23 24 25 26
# 27 28 29 30 31

# >>> print(calObj.formatyear(2017))
# """
def isLegalSpace(x):
	# 2, 2+3, 2+3+3...
	x = x-2
	if x%3==0:
		return True
	return False

def listEntries_year(cwd, year):
	months = os.listdir(year)
	for aMonth in months:
		entries = os.listdir(  os.path.join(year, aMonth)  )
		entries = [_.replace(".txt", "") for _ in entries]
		entries = [_.replace("0", " ") for _ in entries if _.startswith("0")]
		date = str()
		month_num = diaryDateLib._parseMonth(aMonth)
		raw_month_cal = calendar.TextCalendar(firstweekday=6).\
			formatmonth(int(year), month_num).splitlines()
		month_cal = "\n".join(raw_month_cal[:2])
		rows = raw_month_cal[2:]
		for aRow in rows:
			month_cal+= "\n"
			dates_present = list()
			for i, aChar in enumerate(aRow):
				if isLegalSpace(i):
					if date in entries:		dates_present.append(date)
					else:					dates_present.append("--")
					date = str()
				else:
					date+= aChar
			month_cal+= " ".join(dates_present)
		print("".join(month_cal))
	return

def listDiaryEntries(diaryDir):
	with dirBongdi(diaryDir) as cwd:
		dirs = os.listdir(".")
		dirs.remove(".git")	# NOTE: this is fugly
		dirs.remove("README.txt")
		if len(dirs) > 1:
			print("Entries for the following years have been made:")
			[print("\t"+_) for _ in dirs]
			ch_u = input("Which year's entries would you like to see? >>> ")
			ch_i = str(diaryDateLib._parseYear(ch_u))
			if os.path.isdir(ch_i):
				listEntries_year(cwd, ch_i)
			else:
				print("No entries were made for {} (interpreted as {})".format(ch_u, ch_i))
				return
		else:
			listEntries_year(cwd, dirs[0])
	return





"""
http://events.upxacademy.com/online-session?utm_source=AITrlClass&utm_medium=Ads&utm_campaign=AIBanner
https://duckduckgo.com/?q=cervical+orgasm&t=ironbrowser&ia=web
https://torrentproject.se/827f9e2f6f56f835702bcde21b348a1dc6ee7b90/Michael-Stanborough.Direct-Release-Myofascial-Technique-torrent.html
https://torrentz2.me/search?f=Myofascial
https://thepiratebay.org/torrent/4304374/
https://torrentz2.me/search?f=myofascial+technique
https://duckduckgo.com/?q=roxanne+rae+abella+danger&t=ironbrowser&ia=web
http://thebloodsugarsecret.com/sp-lfslv1/?p=
https://www.softwareprojects.com/
http://libgen.io/book/index.php?md5=D3E58D5F1D1499745057942DA830268D
http://www.seductionscience.com/2011/get-manly-and-good-posture-body-language-guide/
"""