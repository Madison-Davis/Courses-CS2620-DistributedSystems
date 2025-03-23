import unittest
import threading
import time
import os
import sqlite3
from concurrent import futures
import grpc

# Import the server code and configuration.
from server import server
from config import config
from comm import chat_pb2, chat_pb2_grpc
from client import chat_client

def start_test_server(fixed_pid):
    """
    Monkey-patches server.get_pid so that the ChatService instance
    uses a fixed PID (and therefore a fixed port, per config.BASE_PORT + pid).
    Starts a gRPC server running the ChatService, and starts its heartbeat loop.
    Returns the (grpc.Server, ChatService) tuple.
    """
    original_get_pid = server.get_pid
    server.get_pid = lambda: fixed_pid
    chat_service = server.ChatService()
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(chat_service, grpc_server)
    port = config.BASE_PORT + fixed_pid
    grpc_server.add_insecure_port(f'{config.HOST}:{port}')
    grpc_server.start()
    chat_service.start_heartbeat()
    server.get_pid = original_get_pid
    return grpc_server, chat_service

class TestReplication(unittest.TestCase):
    def setUp(self):
        # Save original heartbeat settings.
        self.original_interval = config.HEARTBEAT_INTERVAL
        self.original_timeout = config.HEARTBEAT_TIMEOUT
        # Use a faster heartbeat interval but increase timeout so that
        # replicas are not dropped too aggressively.
        config.HEARTBEAT_INTERVAL = 0.5
        config.HEARTBEAT_TIMEOUT = 3.0

        # Start three servers with fixed pids: 0, 1, 2.
        self.servers = {}       # pid -> grpc.Server
        self.chat_services = {} # pid -> ChatService instance
        for pid in [0, 1, 2]:
            srv, cs = start_test_server(pid)
            self.servers[pid] = srv
            self.chat_services[pid] = cs

        # Allow time for the heartbeat loops to initialize.
        time.sleep(2)

    def tearDown(self):
        # Stop all running servers and wait for termination.
        for srv in self.servers.values():
            srv.stop(0).wait()
        # Close all database connections to release file locks.
        for cs in self.chat_services.values():
            try:
                cs.db_connection.close()
            except Exception as e:
                print("Error closing DB connection:", e)
        # Wait briefly to let the OS release file locks.
        time.sleep(1)
        # Remove SQLite database files (retry if necessary).
        for pid in [0, 1, 2]:
            db_file = f"chat_database_{pid}.db"
            if os.path.exists(db_file):
                for _ in range(10):
                    try:
                        os.remove(db_file)
                        break
                    except PermissionError:
                        time.sleep(0.2)
        # Restore heartbeat settings.
        config.HEARTBEAT_INTERVAL = self.original_interval
        config.HEARTBEAT_TIMEOUT = self.original_timeout

    def get_cluster_leader(self):
        """
        Returns the leader PID as seen by the running ChatService instances.
        All surviving servers should agree on the leader.
        """
        leaders = {cs.leader for cs in self.chat_services.values()}
        self.assertEqual(len(leaders), 1, "Surviving servers do not agree on a leader.")
        return leaders.pop()

    def test_replication_create_account(self):
        """
        Verify that a CreateAccount request from the leader is replicated to all servers.
        """
        leader = self.get_cluster_leader()
        self.assertEqual(leader, 0)

        leader_address = f"{config.HOST}:{config.BASE_PORT + leader}"
        client_instance = chat_client.ChatClient(server_address=leader_address)
        username = "testuser"
        password_hash = "dummyhash"
        result = client_instance.create_account(username, password_hash)
        self.assertTrue(result)

        # Wait to allow replication to complete.
        time.sleep(2)

        for pid in [0, 1, 2]:
            db_file = f"chat_database_{pid}.db"
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
            row = cursor.fetchone()
            self.assertIsNotNone(row, f"Account not found in server with pid {pid}")
            self.assertEqual(row[0], username)
            conn.close()

    def test_leader_election(self):
        """
        Verify that when the current leader is killed, the remaining servers elect a new leader.
        """
        leader = self.get_cluster_leader()
        self.assertEqual(leader, 0)

        # Kill leader (pid 0) and remove it.
        self.servers[0].stop(0).wait()
        del self.servers[0]
        del self.chat_services[0]

        # Wait for heartbeat timeouts and leader election.
        time.sleep(6)

        new_leader = self.get_cluster_leader()
        self.assertEqual(new_leader, 1)

        # Kill server with pid 1.
        self.servers[1].stop(0).wait()
        del self.servers[1]
        del self.chat_services[1]

        time.sleep(6)
        final_leader = self.get_cluster_leader()
        self.assertEqual(final_leader, 2)

    def test_client_requests_during_replication(self):
        """
        Verify that while a client issues multiple CreateAccount requests,
        replication continues correctly even when one replica is killed.
        """
        leader = self.get_cluster_leader()
        leader_address = f"{config.HOST}:{config.BASE_PORT + leader}"
        client_instance = chat_client.ChatClient(server_address=leader_address)

        def create_accounts():
            # Create 5 accounts with a 0.5-second delay between each.
            for i in range(5):
                username = f"user_{i}"
                password_hash = f"hash_{i}"
                client_instance.create_account(username, password_hash)
                time.sleep(0.5)

        account_thread = threading.Thread(target=create_accounts)
        account_thread.start()

        # Wait 1 second before killing replica 2.
        time.sleep(1)
        # Kill replica with pid 2 if it exists and if it is not the leader.
        if 2 in self.servers and self.get_cluster_leader() != 2:
            self.servers[2].stop(0).wait()
            del self.servers[2]
            del self.chat_services[2]

        account_thread.join()
        # Wait enough time for all replication to complete.
        time.sleep(7)

        surviving_pids = list(self.servers.keys())
        for pid in surviving_pids:
            db_file = f"chat_database_{pid}.db"
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            for i in range(5):
                username = f"user_{i}"
                cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
                row = cursor.fetchone()
                self.assertIsNotNone(row, f"Account {username} not found in server with pid {pid}")
                self.assertEqual(row[0], username)
            conn.close()

if __name__ == "__main__":
    unittest.main()
