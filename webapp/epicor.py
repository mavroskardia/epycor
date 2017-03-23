import socket
import requests
import datetime

from zeep import Client
from zeep.transports import Transport
from requests_ntlm import HttpNtlmAuth


class NavigatorNode(dict):

	def __init__(self, node):
		super().__init__()
		self['caption'] = node.find('.//Caption').text
		self['outline'] = node.find('.//OutlineNumber').text
		self['node_type'] = node.find('.//NodeType').text


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

		doc = allocations_result.body.GetNavigatorResult._value_1

		return [NavigatorNode(a) for a in doc]


	def get_time_entries(self, fromdate, todate, foruser=None):
		'Returns the list of time entries between "fromdate" and "todate"'

		entries = self.timeclient.service.GetAllTimeEntries(
			self.resourceid, fromdate, todate, fromdate, todate)

		try:
			return entries.TimeList.Time
		except Exception as e:
			print(e)
			return None


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
	fom = datetime.datetime(now.year, now.month, 1)
	lom = datetime.datetime(now.year, now.month + 1, 1) - datetime.timedelta(1)
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
		for e in epicor.get_time_entries(fom, lom):
			print('{}\t{}\t{} hours\t{}'.format(e.ProjectName, e.TimeEntryDate, e.StandardHours, e.WorkComment))
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

