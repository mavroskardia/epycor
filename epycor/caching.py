'Caching logic for Epycor'

import os
import json
import datetime

import keyring
import appdirs

from .epicor import NavigatorNode, DataNode


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

    userid, _ = load_userid_and_domain_from_cache()
    creds_path, allocations_path = _get_filepaths()
    try:
        os.remove(creds_path)
        os.remove(allocations_path)
    except FileNotFoundError:
        # swallow the exception because this most likely means the file does not yet exist
        pass

    keyring.get_keyring().delete_password('epicor', userid)


def store_credentials(userid, password, domain='AD'):
    'Stores the specified credentials in the platform keychain'

    creds_path, _ = _get_filepaths()
    local_keyring = keyring.get_keyring()

    try:
        local_keyring.set_password('epicor', userid, password)
        with open(creds_path, 'w') as creds_file:
            json.dump({
                'userid': userid,
                'domain': domain
            }, creds_file)
    except FileNotFoundError as fnfe:
        print('Failed to store credentials:', fnfe)
    except Exception as e:
        print('Failed to store credentials:', e)
        os.remove(creds_path)
        local_keyring.delete_password('epicor', userid)
        raise


# disabling bad naming linter warning because you can't have more than 3 underscores...
# pylint: disable=C0103
def load_userid_and_domain_from_cache():
    'Pull the cached user info'

    creds_path, _ = _get_filepaths()

    if not os.path.exists(creds_path):
        return None, None

    with open(creds_path) as creds_file:
        creds = json.load(creds_file)

    if not 'userid' in creds or not 'domain' in creds:
        return None, None

    return creds['userid'], creds['domain']


def load_cached_credentials():
    'Load previously cached credentials'

    # "userid" instead of "username" to match Epicor naming scheme.
    userid, domain = load_userid_and_domain_from_cache()

    if not userid:
        return None, None, None

    # see https://pypi.python.org/pypi/keyring for why this is safe
    password = keyring.get_password('epicor', userid)

    return userid, password, domain


def get_cached_allocations():
    'Return deserialized cached allocations'

    _, allocations_path = _get_filepaths()

    if not os.path.exists(allocations_path):
        return None

    with open(allocations_path) as f:
        allocdata = json.load(f)

    cachedate = datetime.datetime.fromtimestamp(float(allocdata['date']))
    delta = datetime.datetime.now() - cachedate

    if delta.days > 3:
        return None

    return allocdata['allocations']


def cache_allocations(allocs):
    'Cache allocations in user cache dir'

    obj = {
        'allocations': allocs,
        'date': datetime.datetime.now().timestamp()
    }

    _, allocations_path = _get_filepaths()

    with open(allocations_path, 'w') as alloc_file:
        json.dump(obj, alloc_file, cls=CustomEncoder)

    return True


def _get_filepaths():

    cache_dir = appdirs.user_cache_dir('epycor')
    creds_path = os.path.join(cache_dir, 'creds.json')
    allocations_path = os.path.join(cache_dir, 'allocations.json')

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    return creds_path, allocations_path
