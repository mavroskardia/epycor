import json

from base64 import b64decode
from datetime import datetime
from flask import Flask, render_template, g

from .epicor import Epicor
from .caching import (load_cached_credentials, get_cached_allocations,
                      cache_allocations, CustomEncoder)


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

    return render_template('index.html')

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

    return json.dumps(charges, cls=CustomEncoder)
