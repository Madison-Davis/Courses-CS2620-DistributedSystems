import grpc
import os
import sys
import sqlite3
import logging
import queue
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.py"))
from concurrent import futures
from comm import chat_pb2
from comm import chat_pb2_grpc
from config import config
import time

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.pid = get_pid()
        self.port = config.BASE_PORT + self.pid
        self.IS_LEADER = (self.pid == 0)
        self.active_servers = {1: 0, 2: 0, 3: 0}       # Dictionary for active replicas -- pid: last heartbeat timestamp
        self.leader = min(self.active_servers)
        print(f"[SERVER {self.pid}] Running on port {self.port}")
        print(f"[SERVER {self.pid}] Identifies leader {self.leader}")
        db_name = f"chat_database_{self.pid}.db"

        self.db_connection = sqlite3.connect(db_name, check_same_thread=False)
        self.initialize_database()
        self.active_users = {}              # Dictionary to store active user streams
        self.message_queues = {}            # Store queues for active users
        self.lock = threading.Lock()

    def initialize_database(self):
        """Creates necessary tables if they do not exist."""
        with self.db_connection: # automatically commit
            cursor = self.db_connection.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                uuid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                pwd TEXT NOT NULL,
                logged_in INTEGER NOT NULL CHECK (logged_in IN (0, 1))
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                sender TEXT NOT NULL,
                msg TEXT NOT NULL,
                checked INTEGER NOT NULL CHECK (checked IN (0, 1)),
                inbox INTEGER NOT NULL CHECK (inbox IN (0, 1))
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                recipient TEXT NOT NULL,
                msg TEXT NOT NULL,
                checked INTEGER NOT NULL CHECK (checked IN (0, 1))
            )
            ''')

    def CreateAccount(self, request, context):
        """
        Creates account for new username.
        Return: GenericResponse (success, message)
        """
        username = request.username
        password_hash = request.password_hash

        self.active_users[username] = context
        if username not in self.message_queues:
            self.message_queues[username] = queue.Queue()
        
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT 1 FROM accounts WHERE username = ?", (username,))
                if cursor.fetchone() is not None:
                    return chat_pb2.GenericResponse(success=False, message="Username already exists")
                cursor.execute("INSERT INTO accounts (username, pwd, logged_in) VALUES (?, ?, 1)", (username, password_hash))
                response = chat_pb2.GenericResponse(success=True, message="Account created successfully")
            # if this server is leader, replicate the operation
            # TODO: do this for all write operations
            if self.IS_LEADER:
                self.replicate_to_replicas("CreateAccount", request)
            return response
        except Exception as e:
            print(f"CreateAccount Exception:, {e}")
            return chat_pb2.GenericResponse(success=False, message="Create account error")
    
    def Login(self, request, context):
        """
        Marks username as logged in, fetches account information.
        Return: LoginResponse (success, message, inbox count, old messages, new messages, drafts)
        """
        username = request.username
        password_hash = request.password_hash

        self.active_users[username] = context
        if username not in self.message_queues:
            self.message_queues[username] = queue.Queue()
        
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT uuid FROM accounts WHERE username = ? AND pwd = ?", (username, password_hash))
                account = cursor.fetchone()
                if account is not None:
                    cursor.execute("UPDATE accounts SET logged_in = 1 WHERE username = ?", (username,))

                    # Populate data of username
                    # Not newly received messages
                    cursor.execute("""
                        SELECT msg_id, username, sender, msg, checked, inbox
                        FROM messages WHERE username = ? AND inbox = 0
                        ORDER BY msg_id DESC
                    """, (username,))
                    old_messages = cursor.fetchall()

                    old_message_list = [
                        {"msg_id": row[0], "username": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in old_messages
                    ]

                    # Newly received messages in inbox
                    cursor.execute("""
                        SELECT msg_id, username, sender, msg, checked, inbox
                        FROM messages WHERE username = ? AND inbox = 1
                        ORDER BY msg_id DESC
                    """, (username,))
                    new_messages = cursor.fetchall()

                    new_message_list = [
                        {"msg_id": row[0], "username": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in new_messages
                    ]

                    # Saved drafts
                    cursor.execute("""
                        SELECT draft_id, username, recipient, msg, checked
                        FROM drafts
                        WHERE username = ?
                        ORDER BY draft_id
                    """, (username,))
                    drafts = cursor.fetchall()

                    draft_list = [
                        {"draft_id": row[0], "username": row[1], "recipient": row[2], "msg": row[3], "checked": row[4]}
                        for row in drafts
                    ]
                                     
                    cursor.execute("UPDATE accounts SET logged_in = 1 WHERE username = ?", (username,))
                    return chat_pb2.LoginResponse(success=True, message="Login successful", inbox_count=len(new_message_list), old_messages=old_message_list, inbox_messages=new_message_list, drafts=draft_list)
                else:
                    print(f"Login Invalid Credentials")
                    return chat_pb2.LoginResponse(success=False, message="Invalid credentials")
        except Exception as e:
            print(f"Login Exception:, {e}")
            return chat_pb2.LoginResponse(success=False, message="Login error")
    
    def GetPassword(self, request, context):
        """
        Checks if user exists, and if so, returns password hash.
        Return: GetPasswordResponse (success, message, pwd_hash)
        """
        username = request.username

        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT pwd FROM accounts WHERE username = ?", (username,))
                pwd_hash = cursor.fetchone()
                if pwd_hash is None:
                    print(f"GetPassword No User")
                    return chat_pb2.GetPasswordResponse(success=False, message="User does not exist")
                else:
                    return chat_pb2.GetPasswordResponse(success=True, message="Password found", password_hash=pwd_hash[0])
        except Exception as e:
            print(f"GetPassword Exception:, {e}")
            return chat_pb2.GetPasswordResponse(success=False, message="Get password error")

    def ListAccounts(self, request, context):
        """
        Fetches all existing usernames.
        Return: list of account usernames
        """
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT username FROM accounts ORDER BY uuid")
                usernames = [row[0] for row in cursor.fetchall()]
                return chat_pb2.ListAccountsResponse(success=True, message="Accounts fetched", usernames=usernames)
        except Exception as e:
            print(f"ListAccounts Exception:, {e}")
            return chat_pb2.ListAccountsResponse(success=False, message="Could not fetch accounts")
    
    def SaveDrafts(self, request, context):
        """
        Saves drafts of username to updated status.
        Return: GenericResponse (success, message)
        """
        username = request.username
        drafts = request.drafts
        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                # Reset drafts
                cursor.execute("DELETE FROM drafts WHERE username = ?", (username,))
                # Add draft to drafts table
                # Note: `username` is the sender
                # Assumes that drafts is a list of dictionaries
                for draft in drafts:
                    recipient = draft.recipient if draft.recipient else "."
                    msg = draft.msg if draft.msg else "."
                    cursor.execute("""
                        INSERT INTO drafts (username, recipient, msg, checked)
                        VALUES (?, ?, ?, ?)
                    """, (username, recipient, msg, 0,))
                return chat_pb2.GenericResponse(success=True, message="Draft saved")
        except Exception as e:
            print(f"SaveDrafts Exception:, {e}")
            return chat_pb2.GenericResponse(success=False, message="Cannot save draft")

    def AddDraft(self, request, context):
        """
        Adds new draft to drafts database.
        Return: AddDraftResponse (success, message, draft ID of new draft)
        """
        username = request.username
        recipient = request.recipient
        msg = request.message
        checked = request.checked
        
        try:
            # Add draft to drafts table
            # Note: `username` is the sender
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO drafts (username, recipient, msg, checked)
                    VALUES (?, ?, ?, ?) RETURNING draft_id
                """, (username, recipient, msg, checked,))
                return chat_pb2.AddDraftResponse(success=True, message="Draft added", draft_id=cursor.fetchone()[0])
        except Exception as e:
            print(f"AddDraft Exception:, {e}")
            return chat_pb2.AddDraftResponse(success=False, message="Cannot add draft")
    
    def CheckMessage(self, request, context):
        """
        Set message as checked
        Return: GenericResponse (success, message)
        """
        username = request.username
        msg_id = request.msg_id

        try:
            # Update checked status
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("UPDATE messages SET checked = 1 WHERE username = ? AND msg_id = ?", (username, msg_id,))
                return chat_pb2.GenericResponse(success=True, message="Message checked as read")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Message unable to check as read")
    
    def DownloadMessage(self, request, context):
        """
        Mark message as downloaded from inbox
        Return: GenericResponse (success, message)
        """
        username = request.username
        msg_id = request.msg_id

        try:
            # Update inbox status
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("UPDATE messages SET inbox = 0 WHERE username = ? AND msg_id = ?", (username, msg_id,))
                return chat_pb2.GenericResponse(success=True, message="Message downloaded from inbox")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Message unable to download from inbox")
    
    def DeleteMessage(self, request, context):
        """
        Delete message from database
        Return: GenericResponse (success, message)
        """
        username = request.username
        msg_id = request.msg_id

        try:
            # Remove message from messages table
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
                return chat_pb2.GenericResponse(success=True, message="Message deleted")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Message unable to delete")
    
    def DeleteAccount(self, request, context):
        """
        Delete account from database
        Return: GenericResponse (success, message)
        """
        username = request.username

        self.active_users.pop(username)
        self.message_queues.pop(username)

        try:
            # Remove messages sent to the username, username's drafts, and user's account information
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM messages WHERE username = ?", (username,))
                cursor.execute("DELETE FROM drafts WHERE username = ?", (username,))
                cursor.execute("DELETE FROM accounts WHERE username = ?", (username,))
                return chat_pb2.GenericResponse(success=True, message="Account and all messages deleted")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Unable to delete account")
    
    def Logout(self, request, context):
        """
        Set username as logged out
        Return: GenericResponse (success, message)
        """
        username = request.username

        self.active_users.pop(username)
        self.message_queues.pop(username)

        try:
            with self.db_connection: # ensures commit or rollback
                cursor = self.db_connection.cursor()
                cursor.execute("UPDATE accounts SET logged_in = 0 WHERE username = ?", (username,))
                return chat_pb2.GenericResponse(success=True, message="Logged out successfully")
        except Exception as e:
            print(f"Logout Exception:, {e}")
            return chat_pb2.GenericResponse(success=False, message="Unable to log out")
        
    def SendMessage(self, request, context):
        """
        Check if recipient exists, delete draft, add message, and notify if online.
        """
        draft_id = request.draft_id
        recipient = request.recipient
        sender = request.sender
        content = request.content
        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()

                # Check if recipient exists
                cursor.execute("SELECT 1 FROM accounts WHERE username = ?", (recipient,))
                if cursor.fetchone() is None:
                    return chat_pb2.SendMessageResponse(success=False, message="Recipient does not exist")
                
                # Delete draft
                cursor.execute("DELETE FROM drafts WHERE draft_id = ?", (draft_id,))

                # Store the message
                cursor.execute("""
                    INSERT INTO messages (username, sender, msg, checked, inbox)
                    VALUES (?, ?, ?, ?, ?) RETURNING msg_id
                """, (recipient, sender, content, 0, 1))
                msg_id = cursor.fetchone()[0]

                # Get the recipient's new inbox count
                cursor.execute("SELECT COUNT(*) FROM messages WHERE username = ? AND inbox = 1", (recipient,))
                new_inbox_count = cursor.fetchone()[0]
                # If recipient is online, push message to their queue
                with self.lock:
                    if recipient in self.active_users:
                        self.message_queues[recipient].put(chat_pb2.ReceiveMessageResponse(
                            msg_id=msg_id,
                            username=recipient,
                            sender=sender,
                            msg=content,
                            inbox_count=new_inbox_count
                        ))

                return chat_pb2.SendMessageResponse(success=True, message="Message sent", msg_id=msg_id)
        except Exception as e:
            print(f"[SERVER {self.pid}] Error sending message: {e}")
            return chat_pb2.SendMessageResponse(success=False, message="Send message error")

    def ReceiveMessageStream(self, request, context):
        username = request.username
        print(f"[SERVER {self.pid}] {username} connected to message stream.")
        # Ensure the user has a queue
        with self.lock:
            if username not in self.message_queues:
                self.message_queues[username] = queue.Queue()
            self.active_users[username] = True

        try:
            while context.is_active():
                try:
                    # Block until a message is available, then send it
                    message = self.message_queues[username].get(timeout=5)  # 5s timeout to check if still active
                    yield message
                except queue.Empty:
                    continue  # No message yet, keep waiting
        except Exception as e:
            print(f"[SERVER {self.pid}] Error in message stream for {username}: {e}")
        finally:
            with self.lock:
                del self.active_users[username]  # Mark user as offline when they disconnect
                del self.message_queues[username]  # Clean up queue
            print(f"[SERVER {self.pid}] {username} disconnected from message stream.")

    def Replicate(self, request, context):
        """
        Called by the leader on a replica to replicate a write operation.
        Deserialize request.payload and call the appropriate local update.
        """
        method = request.method
        print(f"[REPLICA {config.PROCESS_ID}] Received replication request for method {method}")
        # TODO: deserialize request.payload and call appropriate local update
        return chat_pb2.GenericResponse(success=True, message="Replication applied")
    
    def Heartbeat(self, request, context):
        """
        Respond to heartbeat pings.
        For leader: record the heartbeat from the replica.
        """
        replica_id = request.process_id
        self.active_servers[replica_id] = time.time()
        return chat_pb2.HeartbeatResponse(alive=True)
    
    def replicate_to_replicas(self, method_name, request):
        """
        Called by the leader to replicate a write operation to all alive replicas.
        """
        payload = request.SerializeToString()
        replication_request = chat_pb2.ReplicationRequest(method=method_name, payload=payload)
        for replica_id, address in config.REPLICA_ADDRESSES.items():
            if replica_id not in self.active_servers:
                continue
            # Check heartbeat timestamp (if missing or too old, skip this replica)
            last_hb = self.active_servers.get(replica_id, 0)
            if time.time() - last_hb > config.HEARTBEAT_TIMEOUT:
                print(f"[LEADER] Replica {replica_id} heartbeat timed out; removing from alive list.")
                self.active_servers.pop(replica_id, None)
                continue
            try:
                with grpc.insecure_channel(address) as channel:
                    stub = chat_pb2_grpc.ChatServiceStub(channel)
                    rep_response = stub.Replicate(replication_request)
                    if not rep_response.success:
                        print(f"[LEADER] Replication to replica {replica_id} failed: {rep_response.message}")
            except Exception as e:
                print(f"[LEADER] Error replicating to replica {replica_id}: {e}")
    
    def heartbeat_loop(self):
        while True:
            # send heartbeat ping to all active replicas
            for replica_id, address in config.REPLICA_ADDRESSES.items():
                if replica_id not in self.active_servers:
                    continue
                try:
                    with grpc.insecure_channel(address) as channel:
                        stub = chat_pb2_grpc.ChatServiceStub(channel)
                        hb_request = chat_pb2.HeartbeatRequest(process_id=config.PROCESS_ID)
                        response = stub.Heartbeat(hb_request)
                        if response.alive:
                            self.active_servers[replica_id] = time.time()
                except Exception as e:
                    print(f"[LEADER] Heartbeat failed for replica {replica_id}: {e}")
                    self.active_servers.pop(replica_id, None)
            # check which peers have not responded
            current_time = time.time()
            for replica_id in list(self.active_servers.keys()):
                if current_time - self.active_servers[replica_id] > config.HEARTBEAT_TIMEOUT:
                    print(f"Replica {replica_id} is considered dead.")
                    self.active_servers.pop(replica_id, None)
                    if replica_id == self.leader:
                        self.trigger_leader_election()
            time.sleep(config.HEARTBEAT_INTERVAL)

    def start_heartbeat(self):
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    def trigger_leader_election(self):
        """
        Replica with the lowest process ID becomes the new leader.
        """
        active_ids = list(self.active_servers.keys())
        active_ids.append(self.pid)
        new_leader = min(active_ids)
        print(f"[REPLICA {new_leader}] Becoming the new leader.")
        if new_leader == self.pid:
            self.IS_LEADER = True
        # TODO: update state and notify client

    
def get_pid():
    """Read the current PID from config.py and increment it."""
    # Read the current PID value from config.py
    with open(config_file, "r") as f:
        lines = f.readlines()
    pid_line = next((line for line in lines if line.startswith("PID")), None)
    # Extract the PID, remove extra spaces, comments, and ensure it's an integer
    current_pid = int(pid_line.split('=')[1].split('#')[0].strip()) if pid_line else 1
    # Increment the PID and write it back to the config.py file for the next server
    new_pid = current_pid + 1
    with open(config_file, "w") as f:
        for line in lines:
            if line.startswith("PID"):
                f.write(f"PID         = {new_pid}\n")
            else:
                f.write(line)
    return current_pid
        
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_service = ChatService()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(chat_service, server)
    server_port = config.BASE_PORT + config.PID
    server.add_insecure_port(f'{config.HOST}:{server_port}')
    server.start()
    chat_service.start_heartbeat()
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
    