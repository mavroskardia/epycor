import sys
import json

from base64 import b64decode
from datetime import datetime
from flask import Flask, render_template, g, request

from .epicor import Epicor
from .caching import (load_cached_credentials, get_cached_allocations,
                      clear_credentials, store_credentials, cache_allocations,
                      CustomEncoder)


epicorsvc = Epicor(*load_cached_credentials())
app = Flask(__name__)


@app.after_request
def add_no_caching(resp):

    resp.headers['Cache-Control'] = 'public,max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = 0

    return resp


@app.route('/')
def index():

    if not epicorsvc.are_credentials_loaded:
        return render_template('getcreds.html')

    return render_template('index.html')


@app.route('/clearcreds')
def clearcreds():

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

    data = json.loads(request.get_data())

    username = data.get('username')
    password = data.get('password')
    domain = data.get('domain')

    if not username or not password or not domain:
        return json.dumps({
            'error': True,
            'message': 'You have to enter all three fields'
        })

    try:
        store_credentials(username, password, domain)
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

    allocations = get_cached_allocations()

    if not allocations:
        fromdate, todate = [datetime.fromtimestamp(int(a))
                            for a in
                            b64decode(dates.encode()).decode().split('|')]
        allocations = epicorsvc.get_allocations(fromdate, todate)
        cache_allocations(allocations)

    return json.dumps(allocations, cls=CustomEncoder)


@app.route('/charges/<string:dates>')
def charges(dates):

    if not dates:
        return None, 500

    fromdate, todate = [datetime.fromtimestamp(int(a))
                        for a in
                        b64decode(dates.encode()).decode().split('|')]

    charges = epicorsvc.get_time_entries(fromdate, todate)

    print(charges)

    return json.dumps(charges, cls=CustomEncoder), 200


@app.route('/entertime', methods=['POST'])
def entertime():

    data = json.loads(request.get_data())

    task = data.get('task')
    comments = data.get('comments')
    charges = data.get('charges')
    date = data.get('date')

    try:

        epicorsvc.save_time(
            when=date,
            what=task,
            hours=charges,
            comments=comments
        )

    except Exception as e:
        import pdb; pdb.set_trace()
        return json.dumps({'message':e.message}), 500

    return '', 200


@app.route('/deletetime', methods=['POST'])
def deletetime():

    data = json.loads(request.get_data())

    tasks = data.get('tasks')

    try:
        epicorsvc.delete_time(tasks)
    except Exception as e:
        return json.dumps({'message':e.message}), 500

    return '', 200


@app.route('/markforapproval', methods=['POST'])
def markforapproval():

    data = json.loads(request.get_data())

    tasks = data.get('tasks')

    try:
        epicorsvc.mark_for_approval(tasks)
    except Exception as e:
        return json.dumps({'message':e.message}), 500

    return '', 200


