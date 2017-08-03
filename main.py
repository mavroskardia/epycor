'Entrypoint module for Epycor'

import sys
import os
import threading
import datetime
import json

from cefpython3 import cefpython as cef
from dateutil.parser import parse

import epicor
import caching


class Epycor:
    'Encapsulated runner for CEF Epycor'

    def __init__(self):
        self.browser_settings = {'file_access_from_file_urls_allowed': True}
        self.epicor = None
        self.exposed_functions = {
            'store_credentials': self.store_credentials,
            'get_allocations': self.get_allocations,
            'get_charges': self.get_charges,
            'save_charges': self.save_charges,
            'delete_charges': self.delete_charges,
            'markforapproval': self.markforapproval,
            'clear_credentials': self.clear_credentials,
            'exit_epycor': self.exit_epycor
        }

    def set_client_handlers(self, browser):
        'Where we can hook into various aspects of the browser'

        class DisplayHandler:
            'Handle display-related hooks'

            #pylint: disable=C0103
            def OnConsoleMessage(self, browser, message, **_):
                'When something is printed to the console, send it to stdout'
                print('JS: ', message)

        browser.SetClientHandler(DisplayHandler())

    def clear_credentials(self, jscallback):
        'client-facing clear command'
        caching.clear_credentials()
        jscallback.Call()

    def store_credentials(self, username, password, jscallback):
        'Store new credentials and re-instantiate Epicor object'
        caching.store_credentials(username, password)
        self.epicor = epicor.Epicor(username, password)
        jscallback.Call()

    def get_allocations(self, fromdate, todate, jscallback):
        'Get allocations from Epicor and send them client-side'

        def threadfunc(fromdate, todate, jscallback):
            'Threaded so we do not block the UI'
            allocations = caching.get_cached_allocations()
            if not allocations:
                allocations = self.epicor.get_allocations(parse(fromdate), parse(todate))
                caching.cache_allocations(allocations)
                allocations = caching.get_cached_allocations()
            jscallback.Call(allocations)

        thread = threading.Thread(target=threadfunc, args=(fromdate, todate, jscallback))
        thread.start()

    def get_charges(self, fromdate, jscallback):
        'Get charges for the week starting from the time specified'

        def threadfunc(fromdate, jscallback):
            'Non-block thread for UI'
            fromdate = parse(fromdate)
            todate = fromdate + datetime.timedelta(days=6)
            charges = self.epicor.get_time_entries(fromdate, todate)
            jscallback.Call(json.dumps(charges, cls=caching.CustomEncoder))

        thread = threading.Thread(target=threadfunc, args=(fromdate, jscallback))
        thread.start()

    def save_charges(self, payload, jscallback):
        'Parse payload and send to epicor for saving'

        data = json.loads(payload)
        self.epicor.save_time(data['date'], data['task'], data['hours'], data.get('comments', ''))

        jscallback.Call()

    def delete_charges(self, payload, jscallback):
        'Parse payload and send to epicor for deleting'

        tasks = json.loads(payload)
        self.epicor.delete_time(tasks)

        jscallback.Call()

    def markforapproval(self, payload, jscallback):
        'Parse payload and send to epicor for marking for approval'

        tasks = json.loads(payload)
        self.epicor.mark_for_approval(tasks)

        jscallback.Call()

    def exit_epycor(self):
        'Exit app -- not doing this right at the moment'
        cef.Shutdown()

    def set_javascript_bindings(self, browser):
        'Create JS bindings for python functions'

        bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)

        for funcname, func in self.exposed_functions.items():
            bindings.SetFunction(funcname, func)

        browser.SetJavascriptBindings(bindings)

    def main(self):
        'Entrypoint'

        if getattr(sys, 'frozen', False):
            # frozen
            basepath = os.path.dirname(sys.executable)
        else:
            # unfrozen
            basepath = os.path.dirname(os.path.abspath(__file__))

        sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
        cef.Initialize()
        #cef.SetGlobalClientCallback('OnAfterCreated', self.onaftercreated)

        window_info = cef.WindowInfo()
        window_info.SetAsChild(0, [0, 0, 800, 1000])

        username, password, _ = caching.load_cached_credentials()

        baseuri = 'file://{file}'

        if None in (username, password):
            indexfile = 'getcreds.html'
        else:
            indexfile = 'index.html'
            self.epicor = epicor.Epicor(username, password)

        index_uri = baseuri.format(file=os.path.join(basepath, indexfile))

        browser = cef.CreateBrowserSync(url=index_uri,
                                        window_title='Epycor',
                                        window_info=window_info,
                                        settings=self.browser_settings)

        self.set_client_handlers(browser)
        self.set_javascript_bindings(browser)

        if 'debug' in sys.argv:
            browser.ShowDevTools()

        cef.MessageLoop()
        cef.Shutdown()


if __name__ == '__main__':
    Epycor().main()
