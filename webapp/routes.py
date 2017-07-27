'Flask routing module'

import json

from base64 import b64decode
from datetime import datetime
from flask import Flask, render_template, request

from .epicor import Epicor
from .caching import (load_cached_credentials, get_cached_allocations,
                     clear_credentials, store_credentials, cache_allocations,
                     CustomEncoder)


# disabling C0103 due to Flask oddity about module-level variable
# pylint: disable=C0103
epicorsvc = Epicor(*load_cached_credentials())
app = Flask(__name__)


@app.after_request
def add_no_caching(resp):
    'Make sure all requests are set to never cache'

    resp.headers['Cache-Control'] = 'public,max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = 0

    return resp


@app.route('/')
def index():
    'Send user to getcreds to enter credentials or the index page for the app'

    if not epicorsvc.are_credentials_loaded:
        return render_template('getcreds.html')

    return render_template('index.html')


@app.route('/clearcreds')
def clearcreds():
    'Remove all stored credentials and allocations'

    try:
        clear_credentials()
    except Exception as e:
        return json.dumps({
            'error': True,
            'message': e.message
        })

    return json.dumps({
        'error': False,
        'message': 'Successfully cleared credentials'
    })


@app.route('/storecreds', methods=['POST'])
def storecreds():
    'Stores specified credentials'

    data = json.loads(request.get_data())

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return json.dumps({
            'error': True,
            'message': 'You have to enter all three fields'
        })

    try:
        store_credentials(username, password)
    except Exception as e:
        return json.dumps({
            'error': True,
            'message': e.message
        })

    return json.dumps({
        'error': False,
        'message': 'Successfully stored credentials'
    })


@app.route('/allocations/<string:dates>')
def allocations(dates):
    'look for cached allocations and return those, otherwise ask epicor (slow)'

    allocs = get_cached_allocations()

    if not allocs:
        fromdate, todate = [datetime.fromtimestamp(int(a))
                            for a in
                            b64decode(dates.encode()).decode().split('|')]
        allocs = epicorsvc.get_allocations(fromdate, todate)
        import pdb; pdb.set_trace()
        cache_allocations(allocs)

    return json.dumps(allocs, cls=CustomEncoder)


@app.route('/charges/<string:dates>')
def charges(dates):
    'Returns the charges from the base64-encoded "dates" parameter'

    if not dates:
        return None, 500

    fromdate, todate = [datetime.fromtimestamp(int(a))
                        for a in
                        b64decode(dates.encode()).decode().split('|')]

    entries = epicorsvc.get_time_entries(fromdate, todate)

    return json.dumps(entries, cls=CustomEncoder), 200


@app.route('/entertime', methods=['POST'])
def entertime():
    'send new charge(s) to epicor'

    data = json.loads(request.get_data())

    try:

        epicorsvc.save_time(
            when=data.get('date'),
            what=data.get('task'),
            hours=data.get('charges'),
            comments=data.get('comments')
        )

    except Exception as e:
        import pdb; pdb.set_trace()
        return json.dumps({'message': e.message}), 500

    return '', 200


@app.route('/deletetime', methods=['POST'])
def deletetime():
    'remove an existing time entry from epicor'

    data = json.loads(request.get_data())

    tasks = data.get('tasks')

    try:
        epicorsvc.delete_time(tasks)
    except Exception as e:
        return json.dumps({'message': e.message}), 500

    return '', 200


@app.route('/markforapproval', methods=['POST'])
def markforapproval():
    'mark an existing time entry for approval'

    data = json.loads(request.get_data())

    tasks = data.get('tasks')

    try:
        epicorsvc.mark_for_approval(tasks)
    except Exception as e:
        return json.dumps({'message': e.message}), 500

    return '', 200


