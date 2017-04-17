import os
import json
import keyring
import datetime

from .epicor import NavigatorNode, DataNode


class CustomEncoder(json.JSONEncoder):

    def default(self, obj):
        override = not isinstance(obj, NavigatorNode)
        override = override and not isinstance(obj, DataNode)
        if override:
            return super(CustomEncoder, self).default(obj)
        return obj.__dict__


def load_userid_and_domain_from_cache():

    with open('creds.json') as f:
        creds = json.load(f)

    return creds['userid'], creds['domain']


def load_cached_credentials():

    # "userid" instead of "username" to match Epicor naming scheme.
    userid, domain = load_userid_and_domain_from_cache()

    # see https://pypi.python.org/pypi/keyring for why this is safe
    password = keyring.get_password('epicor', userid)

    return userid, password, domain


def get_cached_allocations():

    if not os.path.exists('allocations.json'):
        return None, None

    with open('allocations.json') as f:
        allocdata = json.load(f)

    cachedate = datetime.datetime.fromtimestamp(float(allocdata['date']))
    delta = datetime.datetime.now() - cachedate

    if delta.days > 3:
        # TODO: provide UI feedback that we are re-caching
        return None, None

    return allocdata['allocations']


def cache_allocations(allocs):

    obj = {
        'allocations': add_breadcrumbs(allocs),
        'date': datetime.datetime.now().timestamp()
    }

    with open('allocations.json', 'w') as f:
        json.dump(obj, f, cls=CustomEncoder)

    return True


def add_breadcrumbs(allocs):

    # basic thought is to order the allocations by outline
    # which ought to mean just going back one in the index to
    # find any given node's parent
    allocs = sorted(allocs, key=lambda alloc: alloc.outline)

    for idx, alloc in enumerate(allocs):
        alloc.breadcrumb = list(reversed(
            [allocs[idx-i].caption
             for i,v in
             enumerate(alloc.outline.split('.'))
             if i != 0 and not alloc.outline.startswith('1')])) # skip self and internal

    return allocs
