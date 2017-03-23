import os
import json
import keyring
import datetime


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

    return allocdata['allocations'], allocdata['tree']


def transform_allocations(allocations):
    'walk the flat list and build a structured tree'

    def insert(node, root):
        depth = root

        for part in node['outline'].split('.'):
            try:
                depth = depth[part]
            except KeyError:
                depth[part] = node

    root = {}

    for allocation in allocations:
        insert(allocation, root)

    return root


def cache_allocations(allocs):

    tree = transform_allocations(allocs)

    obj = {
        'allocations': add_breadcrumbs(allocs, tree),
        'tree': tree,
        'date': datetime.datetime.now().timestamp()
    }

    with open('allocations.json', 'w') as f:
        json.dump(obj, f)

    return True


def add_breadcrumbs(allocs, tree):

    newallocs = []

    for a in allocs:
        breadcrumb = []
        outline_parts = a['outline'].split('.')
        node = tree

        # no need to breadcrumb a toplevel node
        if len(outline_parts) == 1:
            continue

        for op in outline_parts:
            node = node[op]

            # don't add self to breadcrumb!
            if node['outline'] == a['outline']:
                break

            breadcrumb.append(node['caption'])

        a['breadcrumb'] = breadcrumb
        newallocs.append(a)

    return newallocs


if __name__ == '__main__':

    allocs = [
        {'outline': '1', 'caption': 'Internal Activities'},
        {'outline': '1.1', 'caption': 'Meetings'},
        {'outline': '1.2', 'caption': 'Bereavment'},
        {'outline': '2', 'caption': '1107'},
        {'outline': '2.1', 'caption': 'Labor'},
        {'outline': '2.1.1', 'caption': 'Task 1'},
        {'outline': '2.1.2', 'caption': 'Task 2'},
        {'outline': '2.2', 'caption': 'Planning'},
        {'outline': '2.2.1', 'caption': 'Proposals'},
    ]

    tree = {
        '1': {
            'caption': 'Internal Activities',
            'outline': '1',
            '1': {
                'caption': 'Meetings',
                'outline': '1.1'
            },
            '2': {
                'caption': 'Bereavment',
                'outline': '1.2'
            }
        },
        '2': {
            'caption': '1107',
            'outline': '2',
            '1': {
                'caption': 'Labor',
                'outline': '2.1',
                '1': {
                    'caption': 'Task 1',
                    'outline': '2.1.1'
                },
                '2': {
                    'caption': 'Task 2',
                    'outline': '2.1.2'
                }
            },
            '2': {
                'caption': 'Planning',
                'outline': '2.2',
                '1': {
                    'caption': 'Proposals',
                    'outline': '2.2.1'
                }
            }
        }
    }

    newallocs = add_breadcrumbs(allocs, tree)

    import pdb; pdb.set_trace()
