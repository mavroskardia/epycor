import sys

from PyQt5.QtCore import QThread, QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView


PORT = 5180
ROOT_URL = 'http://localhost:{}'.format(PORT)


class FlaskThread(QThread):
    def __init__(self, application):
        QThread.__init__(self)
        self.application = application

    def __del__(self):
        self.wait()

    def run(self):
        self.application.run(port=PORT)


def run_gui(application):

    qtapp = QApplication(sys.argv)

    webapp = FlaskThread(application)
    webapp.start()

    qtapp.aboutToQuit.connect(webapp.terminate)

    webview = QWebEngineView()
    webview.load(QUrl(ROOT_URL))
    webview.resize(800,1000)
    webview.setWindowTitle('Epycor')
    webview.setMinimumSize(800, 1000)
    webview.show()

    return qtapp.exec_()


if __name__ == '__main__':

    from webapp.routes import app
    sys.exit(run_gui(app))
