# tests.client



# +++++++++++++ Imports and Installs +++++++++++++ #
import unittest
import sqlite3
import json
import os
import sys
path1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../server'))
path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../client'))
sys.path.append(path1)
sys.path.append(path2)
from server import db_init, process_request
from client import client_conn, gui



# +++++++++++++ Class: TestDatabase ++++++++++++++ #
class TestChatDatabase(unittest.TestCase):
    """ List of all tests on the client + server: """
    pass
    


# ++++++++++++++++ Main Function +++++++++++++++++ #
if __name__ == '__main__':
    unittest.main()
