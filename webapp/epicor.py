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


class TimeEntry(dict):

	def __init__(self, node):
		super().__init__()

		self['time_id'] = self.get(node, 'TimeID')
		self['project_code'] = self.get(node, 'ProjectCode')
		self['task_uid'] = self.get(node, 'TaskUID')
		self['activity_code'] = self.get(node, 'ActivityCode')
		self['resource_id'] = self.get(node, 'ResourceID')
		self['time_entry_date'] = self.get(node, 'TimeEntryDate')
		self['status_code'] = self.get(node, 'StatusCode')
		self['standard_hours'] = self.get(node, 'StandardHours')
		self['overtime_hours'] = self.get(node, 'OvertimeHours')
		self['work_comment'] = self.get(node, 'WorkComment')
		self['status'] = self.get(node, 'Status')
		self['activity_desc'] = self.get(node, 'ActivityDesc')
		self['row_check_flag'] = self.get(node, 'RowCheckFlag')
		self['internal_flag'] = self.get(node, 'InternalFlag')
		self['original'] = self.get(node, 'Original')
		self['project_site_urn'] = self.get(node, 'ProjectSiteURN')
		self['resource_site_urn'] = self.get(node, 'ResourceSiteURN')
		self['project_customer'] = self.get(node, 'ProjectCustomer')
		self['project_name'] = self.get(node, 'ProjectName')
		self['event_code'] = self.get(node, 'EventCode')
		self['event_status_code'] = self.get(node, 'EventStatusCode')
		self['status_flag'] = self.get(node, 'StatusFlag')
		self['create_user_id'] = self.get(node, 'CreateUserID')
		self['create_date'] = self.get(node, 'CreateDate')
		self['last_update_user_id'] = self.get(node, 'LastUpdateUserID')
		self['last_update_date'] = self.get(node, 'LastUpdateDate')
		self['organization_id'] = self.get(node, 'OrganizationID')
		self['origin_flag'] = self.get(node, 'OriginFlag')
		self['resource_long_name'] = self.get(node, 'ResourceLongName')
		self['unassigned_entry_flag'] = self.get(node, 'UnassignedEntryFlag')
		self['hours'] = self.get(node, 'Hours')
		self['work_type_code'] = self.get(node, 'WorkTypeCode')
		self['loc_required_time_entry_flag'] = self.get(node, 'LocRequiredTimeEntryFlag')
		self['project_status'] = self.get(node, 'ProjectStatus')
		self['opportunity_id'] = self.get(node, 'OpportunityID')
		self['time_entry_comment'] = self.get(node, 'TimeEntryComment')
		self['task_rule_notes_flag'] = self.get(node, 'TaskRuleNotesFlag')
		self['project_site_name'] = self.get(node, 'ProjectSiteName')
		self['avoid_update_site'] = self.get(node, 'AvoidUpdateSite')

	def get(self, node, name):

		e = node.find('.//{}'.format(name))
		if e is not None:
			return e.text

		return ''


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

		print('getting time entries from {} to {}'.format(fromdate, todate))

		entries_result = self.timeclient.service.GetAllTimeEntries(
			self.resourceid, fromdate, todate, fromdate, todate)

		doc = entries_result.body.GetAllTimeEntriesResult._value_1

		entries = [TimeEntry(e) for e in doc]

		print('Created', len(entries), 'for that time period')

		return entries


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
			print('{}\t{}\t{} hours\t{}'.format(
				e.project_name or e.activity_code,
				e.time_entry_date,
				e.standard_hours,
				e.work_comment))
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

