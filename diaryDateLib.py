import os
import time

DEVEL = False

getSystemDate = lambda: time.strftime("%d %B, %Y", time.localtime())

def path_to_date(filePath):
	# DEVEL: ---- start ----
	if DEVEL and not os.path.isfile(filePath):
		print("requested file doesn't exists")
		return False
	# DEVEL: ----  end  ----
	filePath = os.path.splitext(filePath)[0] # get rid of trailing EXTN
	filePath = filePath.split(os.sep)
	y, m, d = filePath[-3], filePath[-2], filePath[-1]
	ans = validateDate(y, m, d, persist=False)
	if ans in ["data unfit", "naughty values"]:
		print(os.path.basename(__file__), end=": ")
		print("Bogus values, given file path can't represent a diary entry")
		return False
	return "%s %s, %s" % ans

def date_to_path(date):
	""" 
	Note that both getSystemDate and custom_date follow the following format:
		"dd mmm, yyyy"
	"""
	try:
		d, m, y = date.split(" ")
		m = m[:-1]  # remove the comma
	except:
		return False
	else:
		ans = validateDate(y, m, d, persist=False)
		if ans in ["data unfit", "naughty values"]:
			return False
	return os.sep.join([y, m, d])

def _parseYear(y=None):
	if y is None:               y = input("Enter year: ")
	try:                        int(y)
	except ValueError:          return False
	try:                        year = time.strptime(y, "%y").tm_year
	except ValueError:
		try:                    year = time.strptime(y, "%Y").tm_year
		except ValueError:      return False
	return year

def _parseMonth(m=None):
	if m is None:               m = input("Enter month name: ").title()
	if m.isdecimal():
		if len(m) == 1:         m = "0"+m
		try:                    month = time.strptime(m, "%m").tm_mon
		except ValueError:      return False
	else:
		try:                    month = time.strptime(m, "%b").tm_mon
		except ValueError:
			try:                month = time.strptime(m, "%B").tm_mon
			except ValueError:  return False
	return month

def _parseDate(d=None):
	if d is None:               d = input("Enter date of month: ")
	if len(d) == 1:             d = "0"+d
	try:                        date = time.strptime(d, "%d").tm_mday
	except ValueError:          return False
	return date

def validateDate(y=None, m=None, d=None, persist=True):
	""" if persist is set to true, fn enters interactive mode and doesn't quit
	until correct date is entered
		returns "unfit data" if persist==True && (y, m, d) values are shitty
		returns "naughty values" if well... values are naughty (i.e. parsed
			legally but won't appear in a calendar, e.g. 29 Feb, 2001)
		returns d, m, y tuple when execution is flawless
	"""
	x = tuple(  [_parseYear(y), _parseMonth(m), _parseDate(d)]  )
	if False in x:
		if persist:
			# enter stubborn mode
			del y, m, d
			while True:
				year = _parseYear()
				if year:    break
			while True:
				month = _parseMonth()
				if month:   break
			while True:
				date = _parseDate()
				if date:    break
		else:
			# persist is False and data provided was bad
			return "data unfit"
	else:
		# values of x are individually legal, so unpack x like so:
		year, month, date = x
	bigMonthsNums = [1, 3, 5, 7, 8, 10, 12]
	monthNames = ["January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December"]
	maxDays = 31 if month in bigMonthsNums else \
		(lambda: 30 if month != 2 else \
			(lambda: 29 if year%(lambda: \
					400 if str(year).endswith("00") else 4)()\
			==0 else 28)()
		)()
	if date <= maxDays:
		return (
			"0"+str(date) if date<10 else str(date),
			monthNames[month-1],
			str(year)
		)
	else:
		print("Naughty values provided by user")
		return "naughty values"
	return False

def tests(dev=False):
	if dev:
		globals()["DEVEL"] = True
	print("Developer flag set to: ", DEVEL)
	input('\ngetSystemDate()')
	print(getSystemDate())
	input('\nideal case  --->  date_to_path(getSystemDate())')
	print(date_to_path(getSystemDate()))					# ideal case
	input('\nugly data  --->  date_to_path("31 June, ")')
	print(date_to_path("31 June, "))						# ugly data
	input('\nimpossible value  --->  date_to_path("32 January, 2000")')
	print(date_to_path("32 January, 2000"))					# impossible value
	input('\nideal case  --->  path_to_date(date_to_path(getSystemDate()))')
	print(path_to_date(date_to_path(getSystemDate())))		# ideal case
	input('\nto check DEVEL portion of date_to_path  --->  path_to_date(date_to_path("11 January, 1111"))')
	print(path_to_date(date_to_path("11 January, 1111")))	# to check DEVEL portion of date_to_path
	input('\nugly data  --->  path_to_date("2015\\January\\")')
	print(path_to_date("2015\\January\\"))					# ugly data
	input('\ntricky (False) value  --->  path_to_date("1900\\February\\29")')
	print(path_to_date("1900\\February\\29"))				# tricky (False) value
	return

if __name__ == '__main__':
	tests()
