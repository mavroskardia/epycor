import sys
import socket
import requests
import datetime

from copy import copy
from itertools import zip_longest

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from zeep import Client
from zeep.transports import Transport
from requests_ntlm import HttpNtlmAuth

def get(node, name):

	if not node:
		return ''

	e = node.find('.//{}'.format(name))

	if e is not None:
		return e.text

	return ''

class DataNode:

	def __init__(self, node):

		self.action = ''

		self.ActivityCode = get(node, 'ActivityCode')
		self.ActivityDesc = get(node, 'ActivityDesc')
		self.AvoidUpdateSite = get(node, 'AvoidUpdateSite')
		self.BatchID = get(node, 'BatchID')
		self.CreateDate = get(node, 'CreateDate')
		self.CreateUserID = get(node, 'CreateUserID')
		self.EventCode = get(node, 'EventCode')
		self.EventStatusCode = get(node, 'EventStatusCode')
		self.Favorite = get(node, 'Favorite')
		self.Hours = get(node, 'Hours')
		self.InternalFlag = get(node, 'InternalFlag')
		self.InvoiceComment = get(node, 'InvoiceComment')
		self.LastUpdateDate = get(node, 'LastUpdateDate')
		self.LastUpdateUserID = get(node, 'LastUpdateUserID')
		self.LocationCode = get(node, 'LocationCode')
		self.LocationDesc = get(node, 'LocationDesc')
		self.LocRequiredTimeEntryFlag = get(node, 'LocRequiredTimeEntryFlag')
		self.Meal = get(node, 'Meal')
		self.OpportunityID = get(node, 'OpportunityID')
		self.OrganizationID = get(node, 'OrganizationID')
		self.OriginalTimeID = get(node, 'OriginalTimeID')
		self.OriginFlag = get(node, 'OriginFlag')
		self.OvertimeHours = get(node, 'OvertimeHours')
		self.ProjectCode = get(node, 'ProjectCode')
		self.ProjectCustomer = get(node, 'ProjectCustomer')
		self.ProjectName = get(node, 'ProjectName')
		self.ProjectSiteName = get(node, 'ProjectSiteName')
		self.ProjectSiteURN = get(node, 'ProjectSiteURN')
		self.ProjectStatus = get(node, 'ProjectStatus')
		self.RemoteProjectCode = get(node, 'RemoteProjectCode')
		self.RemoteTimeID = get(node, 'RemoteTimeID')
		self.ResourceID = get(node, 'ResourceID')
		self.ResourceLongName = get(node, 'ResourceLongName')
		self.ResourceSiteURN = get(node, 'ResourceSiteURN')
		self.RowCheckFlag = get(node, 'RowCheckFlag')
		self.StandardHours = get(node, 'StandardHours')
		self.Status = get(node, 'Status')
		self.StatusCode = get(node, 'StatusCode')
		self.StatusComment = get(node, 'StatusComment')
		self.StatusFlag = get(node, 'StatusFlag')
		self.TaskName = get(node, 'TaskName')
		self.TaskRuleNotesFlag = get(node, 'TaskRuleNotesFlag')
		self.TaskUID = get(node, 'TaskUID')
		self.TimeEntryComment = get(node, 'TimeEntryComment')
		self.TimeEntryDate = get(node, 'TimeEntryDate')
		self.TimeGUID = get(node, 'TimeGUID')
		self.TimeID = get(node, 'TimeID')
		self.TimeTypeCode = get(node, 'TimeTypeCode')
		self.TransactionIndex = get(node, 'TransactionIndex')
		self.Travel = get(node, 'Travel')
		self.UnassignedEntryFlag = get(node, 'UnassignedEntryFlag')
		self.WorkComment = get(node, 'WorkComment')
		self.WorkTypeCode = get(node, 'WorkTypeCode')

	def as_xml(self):
		pieces = ['<Time action="{}">'.format(self.action)]

		pieces.extend(['<{}>{}</{}>'.format(v, getattr(self, v), v)
					   for v in vars(self)
					   if v != 'action'])

		pieces.append('</Time>')

		return ''.join(pieces)

	@classmethod
	def fromdict(cls, d):

		node = DataNode(None)

		for key in d:
			setattr(node, key, d[key])

		return node


class NavigatorNode:

	def __init__(self, node):

		self.breadcrumb = ''

		self.caption = get(node, 'Caption')
		self.node_type = get(node, 'NodeType')
		self.outline = get(node, 'OutlineNumber')

		datanode = node.find('.//Data') if node else None

		self.data = DataNode(datanode)


	@classmethod
	def fromdict(cls, d):

		node = NavigatorNode(None)

		for key in d:
			if key == 'data':
				node.data = DataNode.fromdict(d[key])
			else:
				setattr(node, key, d[key])

		return node


class NoCredentialsException(Exception):
	pass

class Epicor:

	def __init__(self, username, password, domain='AD'):
		'''
			username and password are required to access NTLM authenticated
			epicor services
		'''

		self.are_credentials_loaded = username and password and domain

		if not self.are_credentials_loaded:
			return

		try:
			epicor_ip = socket.gethostbyname('epicor')
		except socket.gaierror:
			epicor_ip = socket.gethostbyname('epicor.infotechfl.com')

		domainuser = '{}\\{}'.format(domain, username)

		self.ntlm_auth = HttpNtlmAuth(domainuser, password)
		session = requests.Session()
		session.auth = HttpNtlmAuth(domainuser, password, session)
		transport = Transport(session=session)

		try:
			self.timeclient = Client(
				'http://{}/e4se/Time.asmx?wsdl'.format(epicor_ip),
				transport=transport)
		except Exception as e:
			self.are_credentials_loaded = False
			return

		# import pdb; pdb.set_trace()

		self.psaclient = Client(
			'http://{}/e4se/PSAClientHelper.asmx?wsdl'.format(epicor_ip),
			transport=transport)

		self.resourceclient = Client(
			'http://{}/e4se/Resource.asmx?wsdl'.format(epicor_ip),
			transport=transport)

		self.resourceid = self.get_resource_id(username)

		self.criteria_doc_template = '<ProjectTreeCriteriaDoc><SearchCriteria><TimeExpenseTreeType>T</TimeExpenseTreeType><DisplayTreeType>S</DisplayTreeType><ResourceID>{resourceid}</ResourceID><ResourceSiteURN>E4SE</ResourceSiteURN><CustomerID></CustomerID><OpportunityOnlyCode></OpportunityOnlyCode><ProjectCodes></ProjectCodes><ProjectGroupCode></ProjectGroupCode><OrganizationID></OrganizationID><TaskSeqIDs/><WorkloadCode></WorkloadCode><SiteURN>E4SE</SiteURN><FavoritesTree>0</FavoritesTree><InternalTree>1</InternalTree><CustomTree>1</CustomTree><ResourceCategoryList>\'3\'</ResourceCategoryList><FromDate>{fromdate}</FromDate><ToDate>{todate}</ToDate></SearchCriteria></ProjectTreeCriteriaDoc>'

	def get_resource_id(self, userid):

		result = self.resourceclient.service.GetResourceIDForUserID(userid)
		return result.body.GetResourceIDForUserIDResult

	def get_allocations(self, fromdate, todate):
		'Returns the list of allocations'

		allocations_result = self.psaclient.service.GetNavigator(
			self.criteria_doc_template.format(
				resourceid=self.resourceid,
				fromdate=fromdate.isoformat(),
				todate=todate.isoformat()))

		return [NavigatorNode(node)
				for node in
				allocations_result.body.GetNavigatorResult._value_1]


	def get_time_entries(self, fromdate, todate, foruser=None):
		'Returns the list of time entries between "fromdate" and "todate"'

		fromdate = fromdate.date()
		todate = todate.date()

		entries_result = self.timeclient.service.GetAllTimeEntries(
			self.resourceid, fromdate, todate, fromdate, todate)

		return [DataNode(e)
				for e in
			    entries_result.body.GetAllTimeEntriesResult._value_1]

	def save_time(self, when=None, what=None, hours=None, comments=None):

		if not when or not what or not hours:
			# TODO: handle this more gracefully
			return

		if isinstance(what, dict):
			what = [NavigatorNode.fromdict(what)]

		if isinstance(when, str):
			when = parse(when)

		def make_time(entry, when, numhours):
			time = copy(entry.data)
			time.action = 'newmodified'
			time.Hours = numhours
			time.InternalFlag = '0'
			time.OvertimeHours = '0'
			time.ProjectSiteName = 'E4SE'
			time.ProjectSiteURN = 'E4SE'
			time.ResourceID = self.resourceid
			time.ResourceSiteURN = 'E4SE'
			time.StandardHours = numhours
			time.Status = 'New'
			time.StatusCode = 'N'
			time.TimeEntryDate = when.strftime('%Y-%m-%d')
			time.WorkComment = comments

			if time.ActivityCode:
				time.TaskUID = '-1'
				time.ProjectCode = 'Internal Activities'
				time.ActivityDesc = entry.caption
				time.InternalFlag = '1'
				time.UnassignedEntryFlag = '0'
				time.WorkTypeCode = '0'
				time.LocRequiredTimeEntryFlag = '0'
				time.TaskRuleNotesFlag = '0'

			return time

		etcdoc = '<TimeTaskETCForProject useActionHints="true"/>'
		timesvc = self.timeclient.service

		pieces = ['<TimeList ProxyResourceId="" useActionHints="true">']

		entries_hours = zip_longest(hours, what, fillvalue=what[0])
		days_entries_hours = enumerate(entries_hours)

		for daynum, (numhours, entry) in days_entries_hours:
			numhours = float(numhours.get('hours', 0.0))
			if numhours <= 0.0:
				continue
			whendt = when + relativedelta(days=daynum)
			time = make_time(entry, whendt, numhours)
			pieces.append(time.as_xml())

		pieces.append('</TimeList>')

		timelist = ''.join(pieces)

		return timesvc.UpdateTimeAndTaskETCForTimeEntry(timelist, etcdoc)


	def delete_time(self, tasks):
		'tasks generally will come in as a list of dicts'

		if not tasks:
			return None

		entries = [DataNode.fromdict(t) for t in tasks]

		etcdoc = '<TimeTaskETCForProject useActionHints="true"/>'
		timesvc = self.timeclient.service

		pieces = ['<TimeList ProxyResourceId="" useActionHints="true">']

		for entry in entries:
			entry.ResourceID = self.resourceid
			entry.action = 'deleted'
			entry.StatusCode = 'N'
			entry.Status = 'Entered'
			entry.TimeGUID = ''
			entry.AvoidUpdateSite = '0'
			pieces.append(entry.as_xml())

		pieces.append('</TimeList>')

		timelist = ''.join(pieces)

		return timesvc.UpdateTimeAndTaskETCForTimeEntry(timelist, etcdoc)


	def mark_for_approval(self, tasks):

		if not tasks:
			return None

		entries = [DataNode.fromdict(t) for t in tasks]

		etcdoc = '<TimeTaskETCForProject useActionHints="true"/>'
		timesvc = self.timeclient.service

		pieces = ['<TimeList ProxyResourceId="" useActionHints="true">']

		for entry in entries:
			entry.ResourceID = self.resourceid
			entry.action = 'modified'
			entry.StatusCode = 'E'
			entry.Status = 'Ready for Approval'
			entry.TimeGUID = ''
			pieces.append(entry.as_xml())

		pieces.append('</TimeList>')

		timelist = ''.join(pieces)

		return timesvc.UpdateTimeAndTaskETCForTimeEntry(timelist, etcdoc)


if __name__ == '__main__':

	import sys
	import argparse
	import datetime

	from getpass import getpass

	from epicor import Epicor

	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username')
	parser.add_argument('-p', '--password')
	parser.add_argument('-r', '--resourceid')
	parser.add_argument('-d', '--domain')
	parser.add_argument('-c', '--command')
	args = parser.parse_args()

	username = args.username or input('username: ')
	password = args.password or getpass('password: ')
	domain = args.domain or input('domain: ')
	resourceid = args.resourceid or 'AMARTIN'
	command = args.command or 'entries'

	epicor = Epicor(username, password)

	now = datetime.datetime.now()
	fom = datetime.datetime(now.year, now.month-1, 1)
	lom = datetime.datetime(now.year, now.month, 1) - datetime.timedelta(1)
	fow = datetime.datetime(now.year, now.month, now.day - now.weekday())
	low = fow + datetime.timedelta(7)

	if args.command == 'debug':
		import pdb; pdb.set_trace()
	elif args.command == 'storepass':
		import keyring
		passwd = getpass('{}\'s password: '.format(resourceid))
		keyring.set_password('epicor', resourceid, passwd)
	elif args.command == 'getpass':
		import keyring
		passwd = keyring.get_password('epicor', resourceid)
		if not passwd:
			print('No password stored for {}'.format(resourceid))
		else:
			print('I store the following password for {}: {}'.format(resourceid, passwd))
	elif args.command == 'entries':
		print('Entries:')

		import pdb; pdb.set_trace()

		for e in epicor.get_time_entries(fom, lom):
			print(e.as_xml())
	elif args.command == 'allocations':
		print('Allocations for {}:'.format(resourceid))
		allocations = epicor.get_allocations(fow, low)
		import pdb; pdb.set_trace()
		for a in allocations:
			if not hasattr(a, 'Data'):
				continue
			if a.NodeType.startswith('Internal'):
				print('<Internal>\t{}'.format(a.data.ActivityCode))
			elif a.NodeType == 'Task':
				print('<{}>\t{}'.format(a.data.ProjectCode, a.data.TaskName))
	elif args.command == 'seed':

		print('Retrieving allocations...', end='', flush=True)
		allocations = epicor.get_allocations(fow, low)
		print('done.\nLooking for MEETINGS...', end='', flush=True)
		meetings = [a for a in allocations if a.data.ActivityCode == 'MEETINGS']

		if not meetings:
			print('failed to find MEETINGS.\n')
			sys.exit(1)

		print('done')

		print('Charging one hour to task "MEETINGS" for today...',
			  end='',
			  flush=True)

		result = epicor.save_time(
			when=now,
			what=meetings,
			hours=1,
			comments='Testing saving time')

		import pdb; pdb.set_trace()

		print('done')
