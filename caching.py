'Caching logic for Epycor'

import os
import json
import datetime

import keyring

from epicor import NavigatorNode, DataNode


class CustomEncoder(json.JSONEncoder):
    'Simple custom encoder so json.dumps understands our data objects'

    # following recommended method shouldn't be an error
    #pylint: disable=E0202
    def default(self, o):
        'Give it the right direction for NavigatorNode and DataNode'

        override = not isinstance(o, NavigatorNode)
        override = override and not isinstance(o, DataNode)
        if override:
            return super(CustomEncoder, self).default(o)
        return o.__dict__


def clear_credentials():
    'Clears previously saved credentials and allocations'

    username, _ = load_userid_and_domain_from_cache()
    os.remove('creds.json')
    os.remove('allocations.json')
    keyring.get_keyring().delete_password('epicor', username)


def store_credentials(username, password, domain='AD'):

    local_keyring = keyring.get_keyring()

    try:
        local_keyring.set_password('epicor', username, password)
        with open('creds.json', 'w') as f:
            json.dump({
                'userid': username,
                'domain': domain
            }, f)
    except Exception as e:
        os.remove('creds.json')
        local_keyring.delete_password('epicor', username)
        raise e


def load_userid_and_domain_from_cache():

    if not os.path.exists('creds.json'):
        return None, None

    with open('creds.json') as f:
        creds = json.load(f)

    if not 'userid' in creds or not 'domain' in creds:
        return None, None

    return creds['userid'], creds['domain']


def load_cached_credentials():

    # "userid" instead of "username" to match Epicor naming scheme.
    userid, domain = load_userid_and_domain_from_cache()

    if not userid:
        return None, None, None

    # see https://pypi.python.org/pypi/keyring for why this is safe
    password = keyring.get_password('epicor', userid)

    return userid, password, domain


def get_cached_allocations():

    if not os.path.exists('allocations.json'):
        return None

    with open('allocations.json') as f:
        allocdata = json.load(f)

    cachedate = datetime.datetime.fromtimestamp(float(allocdata['date']))
    delta = datetime.datetime.now() - cachedate

    if delta.days > 3:
        # TODO: provide UI feedback that we are re-caching
        return None

    return allocdata['allocations']


def cache_allocations(allocs):

    obj = {
        'allocations': allocs,
        'date': datetime.datetime.now().timestamp()
    }

    with open('allocations.json', 'w') as f:
        json.dump(obj, f, cls=CustomEncoder)

    return True


# def add_breadcrumbs(allocs):

#     # basic thought is to order the allocations by outline
#     # which ought to mean just going back one in the index to
#     # find any given node's parent
#     allocs = sorted(allocs, key=lambda alloc: alloc.outline)

#     for idx, alloc in enumerate(allocs):
#         alloc.breadcrumb = list(reversed(
#             [allocs[idx-i].caption
#              for i,v in
#              enumerate(alloc.outline.split('.'))
#              if i != 0 and not alloc.outline.startswith('1')])) # skip self and internal

#     return allocs
