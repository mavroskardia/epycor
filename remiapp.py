import sys
import getpass
import argparse
import epicor

import remi.gui as gui

from remi import start, App


class MyApp(App):

    def __init__(self, *args):
        self.args = self.parse_arguments()
        password = getpass.getpass()
        self.epicor = epicor.Epicor(self.args.username, password)
        super(MyApp, self).__init__(*args)

    def parse_arguments(self):

        parser = argparse.ArgumentParser()
        parser.add_argument('--username')
        parser.add_argument('--domain')

        args = parser.parse_args()

        args.username = args.username or getpass.getuser()

        return args

    def main(self):

        container = gui.VBox()
        self.bt = gui.Button('Get Allocations')

        self.bt.set_on_click_listener(self.on_button_pressed)

        container.append(self.bt)

        return container

    def on_button_pressed(self, widget):

        allocations = epicor.get_allocations()


if __name__ == '__main__':

    start(MyApp)
