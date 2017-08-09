'Execute Epicor commands from the command line'
#pylint: disable=W0212
import sys
import datetime

from getpass import getpass
from html import escape

from dateutil.parser import parse
from dateutil import tz

import epicor

class EpicorCLI:
    'Container class for running Epicor commands'

    def __init__(self):
        self.done = False
        self.epicor = None
        self.current_entries = []
        self.charge_start = None
        self.charge_end = None
        self.commands = {
            'help': self.help,
            'quit': self.quit,
            'charges': self.charges,
            'allocations': self.allocations,
            'debug': self.debug,
            'delete': self.delete_charge
        }

    def run(self):
        'Main entrypoint'

        username = input('Username: ')
        password = getpass('Password: ')

        self.epicor = epicor.Epicor(username, password)
        self.done = False

        while not self.done:
            self.commands.get(input('epicor> '), self.noop)()

        return 0

    def get_title(self, node):
        'Returns type-appropriate name'
        return node.ActivityDesc or node.TaskName or '[UNKNOWN ENTRY]'

    def print_charges(self, charge_nodes, start, end):
        'Prints the currently saved charges'
        print('You have {} charges from {} to {}:'.format(len(charge_nodes), start, end))
        for idx, node in enumerate(charge_nodes):
            print('{:5} {:15} {:15} {}'.format(idx,
                                               self.get_title(node),
                                               node.Hours,
                                               node.WorkComment))

    def noop(self):
        'Runs when a user specifies an invalid command'
        print('Unrecognized command. Type "help" for available commands')

    def help(self):
        'Prints the available commands'
        for k in self.commands:
            print('{:15}{}'.format(k, self.commands[k].__doc__))

    def quit(self):
        'Quits the app'
        print('quitting...')
        self.done = True

    def charges(self):
        'Prints charges over time range'
        self.charge_start = parse(input('Start date (in M/D/Y): '))
        self.charge_end = parse(input('End date (in M/D/Y): '))
        self.current_entries = self.epicor.get_time_entries(self.charge_start, self.charge_end)
        self.print_charges(self.current_entries, self.charge_start, self.charge_end)

    def delete_charge(self):
        'Deletes charge at the index of current_charges'
        self.print_charges(self.current_entries, self.charge_start, self.charge_end)
        idx = int(input('Choose charge to delete by index: '))
        result = self.epicor.delete_time([self.current_entries[idx]])
        print(result)

    def allocations(self):
        now = datetime.datetime.now()
        weekstart = now - datetime.timedelta(days=now.isoweekday())
        weekend = weekstart + datetime.timedelta(days=6)
        allocations = self.epicor.get_allocations(weekstart, weekend)
        print('Retrieved {} allocations.'.format(len(allocations)))
        import pdb; pdb.set_trace()
        print('what now?')


    def debug(self):
        import pdb; pdb.set_trace()
        print('entering debug mode')


if __name__ == '__main__':

    sys.exit(EpicorCLI().run())
