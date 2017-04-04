import socket
import requests
import datetime

from zeep import Client
from zeep.transports import Transport
from requests_ntlm import HttpNtlmAuth


class DataNode:

	def __init__(self, node):

		self.action = ''

		self.TimeID = self.get(node, 'TimeID')
		self.TimeGUID = self.get(node, 'TimeGUID')
		self.ProjectCode = self.get(node, 'ProjectCode')
		self.TaskUID = self.get(node, 'TaskUID')
		self.ActivityCode = self.get(node, 'ActivityCode')
		self.ResourceID = self.get(node, 'ResourceID')
		self.StatusCode = self.get(node, 'StatusCode')
		self.StandardHours = self.get(node, 'StandardHours')
		self.OvertimeHours = self.get(node, 'OvertimeHours')
		self.InvoiceComment = self.get(node, 'InvoiceComment')
		self.StatusComment = self.get(node, 'StatusComment')
		self.WorkComment = self.get(node, 'WorkComment')
		self.Status = self.get(node, 'Status')
		self.TaskName = self.get(node, 'TaskName')
		self.ActivityDesc = self.get(node, 'ActivityDesc')
		self.RowCheckFlag = self.get(node, 'RowCheckFlag')
		self.InternalFlag = self.get(node, 'InternalFlag')
		self.OriginalTimeID = self.get(node, 'OriginalTimeID')
		self.ProjectSiteURN = self.get(node, 'ProjectSiteURN')
		self.ResourceSiteURN = self.get(node, 'ResourceSiteURN')
		self.RemoteTimeID = self.get(node, 'RemoteTimeID')
		self.ProjectCustomer = self.get(node, 'ProjectCustomer')
		self.TimeTypeCode = self.get(node, 'TimeTypeCode')
		self.BatchID = self.get(node, 'BatchID')
		self.ProjectName = self.get(node, 'ProjectName')
		self.TransactionIndex = self.get(node, 'TransactionIndex')
		self.EventCode = self.get(node, 'EventCode')
		self.EventStatusCode = self.get(node, 'EventStatusCode')
		self.StatusFlag = self.get(node, 'StatusFlag')
		self.LocationCode = self.get(node, 'LocationCode')
		self.LocationDesc = self.get(node, 'LocationDesc')
		self.CreateUserID = self.get(node, 'CreateUserID')
		self.CreateDate = self.get(node, 'CreateDate')
		self.LastUpdateUserID = self.get(node, 'LastUpdateUserID')
		self.LastUpdateDate = self.get(node, 'LastUpdateDate')
		self.OrganizationID = self.get(node, 'OrganizationID')
		self.OriginFlag = self.get(node, 'OriginFlag')
		self.ResourceLongName = self.get(node, 'ResourceLongName')
		self.Meal = self.get(node, 'Meal')
		self.Travel = self.get(node, 'Travel')
		self.UnassignedEntryFlag = self.get(node, 'UnassignedEntryFlag')
		self.Hours = self.get(node, 'Hours')
		self.WorkTypeCode = self.get(node, 'WorkTypeCode')
		self.LocRequiredTimeEntryFlag = self.get(node, 'LocRequiredTimeEntryFlag')
		self.ProjectStatus = self.get(node, 'ProjectStatus')
		self.OpportunityID = self.get(node, 'OpportunityID')
		self.Favorite = self.get(node, 'Favorite')
		self.TimeEntryComment = self.get(node, 'TimeEntryComment')
		self.TaskRuleNotesFlag = self.get(node, 'TaskRuleNotesFlag')
		self.RemoteProjectCode = self.get(node, 'RemoteProjectCode')
		self.ProjectSiteName = self.get(node, 'ProjectSiteName')
		self.AvoidUpdateSite = self.get(node, 'AvoidUpdateSite')

	def get(self, node, name):

		if not node:
			return ''

		e = node.find('.//{}'.format(name))

		if e is not None:
			return e.text

		return ''

	def as_xml(self):
		pieces = ['<Time action="{}">'.format(self.action)]

		attribs = vars(self)
		del attribs['action']

		for v in attribs:
			pieces.append('<{}>{}</{}>'.format(v, getattr(self, v), v))

		pieces.append('</Time>')

		return ''.join(pieces)

class NavigatorNode:

	def __init__(self, node):

		self.data = DataNode(node.find('.//Data'))

		self['caption'] = self.get(node, 'Caption')
		self['outline'] = self.get(node, 'OutlineNumber')
		self['node_type'] = self.get(node, 'NodeType')


class Epicor:

	def __init__(self, username, password, domain='AD'):
		'''
			username and password are required to access NTLM authenticated
			epicor services
		'''

		try:
			epicor_ip = socket.gethostbyname('epicor')
		except socket.gaierror:
			epicor_ip = socket.gethostbyname('epicor.infotechfl.com')

		domainuser = '{}\\{}'.format(domain, username)

		self.ntlm_auth = HttpNtlmAuth(domainuser, password)
		session = requests.Session()
		session.auth = HttpNtlmAuth(domainuser, password, session)
		transport = Transport(session=session)

		self.timeclient = Client(
			'http://{}/e4se/Time.asmx?wsdl'.format(epicor_ip),
			transport=transport)

		import pdb; pdb.set_trace()

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

		entries_result = self.timeclient.service.GetAllTimeEntries(
			self.resourceid, fromdate, todate, fromdate, todate)

		return [DataNode(e)
			    for e in
			    entries_result.body.GetAllTimeEntriesResult._value_1]

	def save_time(self, entries):
		'''
			An entry is expected to include the task data, date, hours, and
		   	comments
	    '''

		etcdoc = '<TimeTaskETCForProject useActionHints="true"/>'
		pieces = ['<TimeList ProxyResourceId="" useActionHints="true">']

		for entry in entries:
			pieces.append(make_time(entry).as_xml())

		pieces.append('</TimeList>')

		timelist = ''.join(pieces)


if __name__ == '__main__':

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
				print('<Internal>\t{}'.format(a.Data.ActivityCode))
			elif a.NodeType == 'Task':
				print('<{}>\t{}'.format(a.Data.ProjectCode, a.Data.TaskName))
	elif args.command == 'seed':
		print('Charging one hour to task "MEETINGS" for today...',
			  end='',
			  flush=True)

		result = epicor.save_time(now, 'Meetings', )

		import pdb; pdb.set_trace()

		print('done')
