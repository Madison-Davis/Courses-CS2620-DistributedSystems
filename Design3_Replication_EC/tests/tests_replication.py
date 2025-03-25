import unittest
import subprocess
import time
import os
import shutil
import sys

# Ensure the parent directory is in sys.path to import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.chat_client import ChatClient
from server.server_security import hash_password
from config import config

BASE_HOST = "127.0.0.1"
BASE_PORT = config.BASE_PORT  # typically 12300
SERVER_SCRIPT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "server", "server.py")
DATABASE_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "database")

def start_server(pid):
    """
    Starts a server process with a given PID.
    The server listens on BASE_PORT + pid.
    Redirects stdout/stderr to DEVNULL to avoid resource warnings.
    """
    proc = subprocess.Popen(
        ["python", SERVER_SCRIPT, "--pid", str(pid), "--host", BASE_HOST],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return proc

def kill_server(proc):
    """
    Terminates the server process gracefully.
    """
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

class TestReplication(unittest.TestCase):

    def setUp(self):
        """
        Clean up the database folder before each test.
        """
        if os.path.exists(DATABASE_DIR):
            shutil.rmtree(DATABASE_DIR)
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self.servers = []

    def tearDown(self):
        """
        Terminate all server processes that are still running.
        """
        for proc in self.servers:
            try:
                kill_server(proc)
            except Exception:
                pass
        self.servers = []

    def start_servers(self, pids):
        """
        Helper function to start multiple servers.
        """
        procs = []
        for pid in pids:
            proc = start_server(pid)
            procs.append(proc)
            self.servers.append(proc)
        # Allow servers some time to start up
        time.sleep(2)
        return procs

    def test_persistent_storage(self):
        """
        Test persistent storage:
        - Start 3 servers.
        - Create an account via the client.
        - Kill all servers.
        - Restart the 3 servers.
        - Verify that the account still exists.
        """
        # Start servers with PIDs 0, 1, and 2.
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "persistent_user"
        password = "password123"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        # Allow replication to complete.
        time.sleep(2)

        # Kill all servers.
        for proc in list(self.servers):
            kill_server(proc)
            self.servers.remove(proc)
        time.sleep(2)

        # Restart the 3 servers.
        self.start_servers([0, 1, 2])
        time.sleep(2)

        # Create a new client to check persistent state.
        client2 = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        accounts = client2.list_accounts()
        self.assertIn(username, accounts, "Account did not persist after server restart")

    def test_two_fault_tolerance_1(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 1,2.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 1 and PID 2).
        if len(self.servers) >= 3:
            kill_server(self.servers[1])
            kill_server(self.servers[2])
            # Retain only the first server (leader).
            self.servers = [self.servers[0]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_two_fault_tolerance_2(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 0,2.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 0 and PID 2).
        if len(self.servers) >= 3:
            kill_server(self.servers[0])
            kill_server(self.servers[2])
            # Retain only server 1.
            self.servers = [self.servers[1]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_two_fault_tolerance_3(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 0,1.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 0 and PID 1).
        if len(self.servers) >= 3:
            kill_server(self.servers[0])
            kill_server(self.servers[1])
            # Retain only server 2.
            self.servers = [self.servers[2]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_two_fault_tolerance_4(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 1,0.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 1 and PID 0).
        if len(self.servers) >= 3:
            kill_server(self.servers[1])
            kill_server(self.servers[0])
            # Retain only server 2.
            self.servers = [self.servers[2]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_two_fault_tolerance_5(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 2,0.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 2 and PID 0).
        if len(self.servers) >= 3:
            kill_server(self.servers[2])
            kill_server(self.servers[0])
            # Retain only server 1.
            self.servers = [self.servers[1]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_two_fault_tolerance_6(self):
        """
        Test 2-fault tolerance:
        - Start 3 servers.
        - Create an account and record state.
        - Kill servers 2,1.
        - Verify that the client still sees the same state.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "fault_tolerance_user"
        password = "password456"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        accounts_before = client.list_accounts()
        self.assertIn(username, accounts_before, "Account not found before fault injection")

        # Kill 2 servers (e.g., those with PID 2 and PID 1).
        if len(self.servers) >= 3:
            kill_server(self.servers[2])
            kill_server(self.servers[1])
            # Retain only server 0.
            self.servers = [self.servers[0]]
        time.sleep(2)

        # Verify that the state is unchanged.
        accounts_after = client.list_accounts()
        self.assertEqual(accounts_before, accounts_after, "State changed after two servers were killed")

    def test_adding_new_server(self):
        """
        Test adding a new server:
        - Start 3 servers.
        - Create an account.
        - Start a new server (PID 3).
        - Verify that the new server replicates the account data.
        """
        self.start_servers([0, 1, 2])
        client = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+0}")
        username = "new_server_user"
        password = "password789"
        password_hash_value = hash_password(password)
        success = client.create_account(username, password_hash_value)
        self.assertTrue(success, "Account creation failed")
        time.sleep(2)

        # Add a new server with PID 3.
        new_server = start_server(3)
        self.servers.append(new_server)
        # Allow some extra time for the new server to replicate data.
        time.sleep(3)

        # Create a client directed to the new server.
        client_new = ChatClient(server_address=f"{BASE_HOST}:{BASE_PORT+3}")
        accounts_new = client_new.list_accounts()
        self.assertIn(username, accounts_new, "New server did not replicate account data")

if __name__ == '__main__':
    unittest.main()
