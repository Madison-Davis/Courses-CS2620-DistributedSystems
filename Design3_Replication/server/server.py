# server.py



# +++++++++++++ Imports and Installs +++++++++++++ #
import re
import os
import sys
import grpc
import time
import shutil
import sqlite3
import logging
import queue
import threading
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.py"))
database_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
from concurrent import futures
from comm import chat_pb2
from comm import chat_pb2_grpc
from config import config



# ++++++++++++++  Class Definition  ++++++++++++++ #
class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, pid, host):
        """
        Set up ChatService.
        """
        self.active_users = {}                  # Dictionary to store active user streams
        self.message_queues = {}                # Store queues for active users
        self.lock = threading.Lock()            # Lock for receive message threads
        
        # Identify PID and address
        self.pid = pid
        self.port = config.BASE_PORT + self.pid
        self.addr = str(host) + ":" + str(self.port)
        print(f"[SERVER {self.pid}] Running on address {self.addr}")

        # Identify leader
        self.IS_LEADER = (self.pid == 0)
        self.leader = min(config.STARTING_ADDRESSES.keys())
        print(f"[SERVER {self.pid}] Identifies leader {self.leader}")

        # Initialize databases and print starting info
        os.makedirs(database_folder, exist_ok=True)  
        self.db_name = os.path.join(database_folder, f"chat_database_{self.pid}.db")
        self.db_connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.initialize_database()
        self.print_SQL()

    def print_SQL(self):
        """
        Print out server registry table contents.
        """
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT pid, timestamp, addr FROM registry")
            rows = cursor.fetchall()  # Fetch all rows from the table
            if rows:
                print("Registry Table Contents:")
                for row in rows:
                    pid, timestamp, addr = row
                    print(f"PID: {pid}, Timestamp: {timestamp}, Address: {addr}")
            else:
                print("No entries found in the registry.")

    def initialize_database(self):
        """
        Creates necessary tables if they do not exist.
        """
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

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS registry (
                pid INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                addr TEXT NOT NULL
            )
            ''')

            # Clear only the registry table
            cursor.execute("DELETE FROM registry")
            # Insert into registry table
            cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", (0, time.time(), config.STARTING_ADDRESSES[0]))
            cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", (1, time.time(), config.STARTING_ADDRESSES[1]))
            cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", (2, time.time(), config.STARTING_ADDRESSES[2]))

    def update_all_registries(self):
        """
        Notify the leader about the new database creation.
        This can be done via gRPC or another form of communication.
        """
        # Get the leader's address
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT addr FROM registry WHERE pid = ?", (self.leader,))
            leader_addr = cursor.fetchone()
            print(leader_addr)
        # Send a message to the leader
        with grpc.insecure_channel(f"{config.HOST}:{config.BASE_PORT + self.leader}") as channel:
            stub = chat_pb2_grpc.ChatServiceStub(channel)
            request = chat_pb2.UpdateRegistryRequest(
                pid=self.pid,
                timestamp=time.time(),
                addr=self.addr
            )
            response = stub.UpdateRegistry(request)
            if response.success:
                print(f"[SERVER {self.pid}] Leader notified and successful change.")
            else:
                print(f"[SERVER {self.pid}] Leader notified and NOT successful change. {response.message}")

    def UpdateRegistry(self, request, context):
        """
        Leader is notified of the registry change and tells all replicas to update.
        """
        try:
            with self.db_connection:
                cursor = self.db_connection.cursor()
                # Printing the request object fields for debugging
                print(f"Received request: PID={request.pid}, Timestamp={request.timestamp}, Addr={request.addr}")
                # Inserting into the database
                cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", 
                            (request.pid, request.timestamp, request.addr))
                # Replicating to other replicas
                self.print_SQL()
                self.replicate_to_replicas("UpdateRegistry", request)
            return chat_pb2.GenericResponse(success=True, message="success")
        except Exception as e:
            print(f"Error in UpdateRegistry: {e}")
            return chat_pb2.GenericResponse(success=False, message=f"UpdateRegistry error: {e}")

    def UpdateRegistryReplica(self, request, context):
        """
        Replica is notified of the registry change and updates itself.
        """
        try:
            with self.db_connection:  # automatically commit
                cursor = self.db_connection.cursor()
                print(f"Received request for Replica: PID={request.pid}, Timestamp={request.timestamp}, Addr={request.addr}")
                cursor.execute("INSERT INTO registry (pid, timestamp, addr) VALUES (?, ?, ?)", 
                            (request.pid, request.timestamp, request.addr))
            return chat_pb2.GenericResponse(success=True, message="success")
        except Exception as e:
            print(f"Error in UpdateRegistryReplica: {e}")
            return chat_pb2.GenericResponse(success=False, message=f"UpdateRegistryReplica {e}")

    def copy_leader_database(self, pid):
        """
        Copies the database from replica 'pid' to this replica
        """
        try:
            os.makedirs(database_folder, exist_ok=True)  
            pid_db_name = os.path.join(database_folder, f"chat_database_{pid}.db")
            shutil.copy(pid_db_name, self.db_name)
            print(f"[SERVER {self.pid}] Copied database from {pid} to {self.pid}")
        except FileNotFoundError:
            print(f"[SERVER {self.pid}] No previous leader database found. Starting fresh.")
        except Exception as e:
            print(f"[SERVER {self.pid}] Error copying database: {e}")

    def sync_leader_with_latest_database(self):
        """
        If pid=0 is starting and there are existing databases, sync with the latest modified one.
        All other pids will proceed as normal, copying their database over from pid=0
        """
        # List all existing databases, excluding the db with pid 0
        db_files = [os.path.join(database_folder, f) for f in os.listdir(database_folder)]
        db_files = [f for f in db_files if f != self.db_name]
        if len(db_files) > 0:
            # Find the most recently modified database
            latest_db = max(db_files, key=os.path.getmtime)
            match = re.search(r"chat_database_(\d+)\.db", latest_db)
            db_number = int(match.group(1))
            # Sync leader database with the latest one
            shutil.copy(latest_db, self.db_name)
            print(f"[SERVER {self.pid}] Synced database from latest modified {db_number}")
        else:
            print(f"[SERVER {self.pid}] No other database to sync with, keeping database as is")

    def CreateAccount(self, request, context):
        """
        Creates account for new username.
        Return: GenericResponse (success, message)
        """
        username = request.username
        password_hash = request.password_hash

        if context is not None:
            self.active_users[username] = context
        else:
            self.active_users[username] = ""
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
            if self.IS_LEADER:
                self.replicate_to_replicas("CreateAccount", request)
            return response
        except Exception as e:
            print(f"[SERVER {self.pid}] CreateAccount Exception:, {e}")
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
                    response = chat_pb2.LoginResponse(success=True, message="Login successful", inbox_count=len(new_message_list), old_messages=old_message_list, inbox_messages=new_message_list, drafts=draft_list)
                    if self.IS_LEADER:
                        self.replicate_to_replicas("Login", request)
                    return response
                else:
                    print(f"[SERVER {self.pid}] Login Invalid Credentials!")
                    return chat_pb2.LoginResponse(success=False, message="Invalid credentials")
        except Exception as e:
            print(f"[SERVER {self.pid}] Login Exception: {e}")
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
                    return chat_pb2.GetPasswordResponse(success=False, message="User does not exist")
                else:
                    response = chat_pb2.GetPasswordResponse(success=True, message="Password found", password_hash=pwd_hash[0])
                    return response
        except Exception as e:
            print(f"[SERVER {self.pid}] GetPassword Exception: {e}")
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
                response = chat_pb2.ListAccountsResponse(success=True, message="Accounts fetched", usernames=usernames)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] ListAccounts Exception: {e}")
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
                response = chat_pb2.GenericResponse(success=True, message="Draft saved")
                if self.IS_LEADER:
                    self.replicate_to_replicas("SaveDrafts", request)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] SaveDrafts Exception: {e}")
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
                response = chat_pb2.AddDraftResponse(success=True, message="Draft added", draft_id=cursor.fetchone()[0])
                if self.IS_LEADER:
                    self.replicate_to_replicas("AddDraft", request)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] AddDraft Exception: {e}")
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
                response = chat_pb2.GenericResponse(success=True, message="Message checked as read")
                if self.IS_LEADER:
                    self.replicate_to_replicas("CheckMessage", request)
                return response
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
                response = chat_pb2.GenericResponse(success=True, message="Message downloaded from inbox")
                if self.IS_LEADER:
                    self.replicate_to_replicas("DownloadMessage", request)
                return response
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
                response = chat_pb2.GenericResponse(success=True, message="Message deleted")
                if self.IS_LEADER:
                    self.replicate_to_replicas("DeleteMessage", request)
                return response
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
                response = chat_pb2.GenericResponse(success=True, message="Account and all messages deleted")
                if self.IS_LEADER:
                    self.replicate_to_replicas("DeleteAccount", request)
                return response
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
                response = chat_pb2.GenericResponse(success=True, message="Logged out successfully")
                if self.IS_LEADER:
                    self.replicate_to_replicas("Logout", request)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] Logout Exception: {e}")
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

                response = chat_pb2.SendMessageResponse(success=True, message="Message sent", msg_id=msg_id)
                if self.IS_LEADER:
                    self.replicate_to_replicas("SendMessage", request)
                return response
        except Exception as e:
            print(f"[SERVER {self.pid}] SendMessage Exception: {e}")
            return chat_pb2.SendMessageResponse(success=False, message="Send message error")

    def ReceiveMessageStream(self, request, context):
        """
        Fire when a replica receives a message.
        """
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
            # If they just logged out, then self.message_queue[username] will throw {e}, ignore
            # Otherwise, it's a real exception we care about
            print(f"[SERVER {self.pid}] ReceiveMessageStream Exception: {e} (Note a logout/delete occurred if Exception=username)")
        finally:
            with self.lock:
                self.active_users.pop(username, None)    # Mark user as offline when they disconnect
                self.message_queues.pop(username, None)  # Clean up queue
            print(f"[SERVER {self.pid}] {username} disconnected from message stream.")

    def Replicate(self, request, context):
        """
        Called by the leader on a replica to replicate a write operation.
        Deserialize request.payload and call the appropriate local update.
        """
        method = request.method
        print(f"[SERVER {self.pid}] Received replication request for method {method}")
        # Deserialize request.payload and call appropriate local update
        if method == "CreateAccount":
            local_request = chat_pb2.CreateAccountRequest()
            local_request.ParseFromString(request.payload)
            self.CreateAccount(local_request, context)
        elif method == "Login":
            local_request = chat_pb2.LoginRequest()
            local_request.ParseFromString(request.payload)
            self.Login(local_request, context)
        elif method == "SaveDrafts":
            local_request = chat_pb2.SaveDraftsRequest()
            local_request.ParseFromString(request.payload)
            self.SaveDrafts(local_request, context)
        elif method == "AddDraft":
            local_request = chat_pb2.AddDraftRequest()
            local_request.ParseFromString(request.payload)
            self.AddDraft(local_request, context)
        elif method == "CheckMessage":
            local_request = chat_pb2.CheckMessageRequest()
            local_request.ParseFromString(request.payload)
            self.CheckMessage(local_request, context)
        elif method == "DownloadMessage":
            local_request = chat_pb2.DownloadMessageRequest()
            local_request.ParseFromString(request.payload)
            self.DownloadMessage(local_request, context)
        elif method == "DeleteMessage":
            local_request = chat_pb2.DeleteMessageRequest()
            local_request.ParseFromString(request.payload)
            self.DeleteMessage(local_request, context)
        elif method == "DeleteAccount":
            local_request = chat_pb2.DeleteAccountRequest()
            local_request.ParseFromString(request.payload)
            self.DeleteAccount(local_request, context)
        elif method == "Logout":
            local_request = chat_pb2.LogoutRequest()
            local_request.ParseFromString(request.payload)
            self.Logout(local_request, context)
        elif method == "SendMessage":
            local_request = chat_pb2.SendMessageRequest()
            local_request.ParseFromString(request.payload)
            self.SendMessage(local_request, context)
        elif method == "UpdateRegistry":
            local_request = chat_pb2.UpdateRegistryRequest()
            local_request.ParseFromString(request.payload)
            self.UpdateRegistryReplica(local_request, context)
        return chat_pb2.GenericResponse(success=True, message="Replication applied")
    
    def Heartbeat(self, request, context):
        """
        Respond to heartbeat pings.
        For leader: record the heartbeat from the replica.
        """
        return chat_pb2.HeartbeatResponse(alive=True)
    
    def GetLeader(self, request, context):
        """
        Returns the current leader's address.
        Assumes a global variable CURRENT_LEADER that is maintained via heartbeats and election.
        """
        # Look up the current leader's address
        leader_address = config.STARTING_ADDRESSES.get(self.leader, "")
        return chat_pb2.GetLeaderResponse(success=True, leader_address=leader_address)
    
    def replicate_to_replicas(self, method_name, request):
        """
        Called by the leader to replicate a write operation to all alive replicas.
        """
        payload = request.SerializeToString()
        replication_request = chat_pb2.ReplicationRequest(method=method_name, payload=payload)
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT pid, addr FROM registry")
            for replica_id, addr in cursor.fetchall():
                if replica_id == self.leader:
                    continue
                # Check heartbeat timestamp (if missing or too old, skip this replica)
                cursor.execute("SELECT timestamp FROM registry WHERE pid = ? AND addr = ?", (replica_id, addr))
                last_hb = cursor.fetchone()[0]  # Fetch the result (single row)
                if time.time() - last_hb > config.HEARTBEAT_TIMEOUT:
                    print(f"[SERVER {self.pid}] Replica {replica_id} heartbeat timed out; removing from alive list.")
                    continue
                # Send replication request to all active servers
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = chat_pb2_grpc.ChatServiceStub(channel)
                        rep_response = stub.Replicate(replication_request)
                        if not rep_response.success:
                            print(f"[SERVER {self.pid}] Replication to replica {replica_id} failed: {rep_response.message}")
                except Exception as e:
                    print(f"[SERVER {self.pid}] Error replicating to replica {replica_id}: {e}")
    
    def heartbeat_loop(self):
        """
        Create a loop to send and receive heartbeats.
        """
        time.sleep(1)
        while True:
            # send heartbeat ping to all active replicas
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT pid, addr FROM registry")
                for replica_id, addr in cursor.fetchall():
                    # don't send to yourself
                    if replica_id == self.pid:
                        cursor.execute("UPDATE registry SET timestamp = ? WHERE pid = ?", (time.time(), replica_id,))
                        continue
                    # try sending to other channel
                    try:
                        with grpc.insecure_channel(addr) as channel:
                            stub = chat_pb2_grpc.ChatServiceStub(channel)
                            hb_request = chat_pb2.HeartbeatRequest()
                            response = stub.Heartbeat(hb_request)
                            # if alive, update DB
                            if response.alive:
                                with self.db_connection:
                                    cursor = self.db_connection.cursor()
                                    cursor.execute("UPDATE registry SET timestamp = ? WHERE pid = ?", (time.time(), replica_id,))
                                print(f"[SERVER {self.pid}] Replica {replica_id} is alive!")
                                self.print_SQL()
                    except Exception as e:
                        print(f"[SERVER {self.pid}] Heartbeat failed for replica {replica_id}.  Trying again...")
            # check which peers have not responded
            current_time = time.time()
            with self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT pid FROM registry")
                pids = cursor.fetchall()
                for replica_id in pids:
                    replica_id = replica_id[0]
                    if replica_id == self.pid:
                        continue
                    cursor.execute("SELECT timestamp FROM registry WHERE pid = ?", (replica_id,))
                    last_hb = cursor.fetchone()[0]  # Fetch the result (single row)
                    if current_time - last_hb > config.HEARTBEAT_TIMEOUT:
                        print(f"[SERVER {self.pid}] Replica {replica_id} is considered dead. {current_time} {last_hb, {current_time-last_hb}}")
                        # let replicas remove the registry (if already deleted, ignore)
                        # If dead and in the list, remove it
                        with self.db_connection:
                            cursor = self.db_connection.cursor()
                            cursor.execute("DELETE FROM registry WHERE pid = ?", (replica_id,))
                        if replica_id == self.leader:
                            self.trigger_leader_election()
                        self.print_SQL()
            time.sleep(config.HEARTBEAT_INTERVAL)

    def start_heartbeat(self):
        """
        Start the heartbeat loop.
        """
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    def trigger_leader_election(self):
        """
        Replica with the lowest process ID becomes the new leader.
        """
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT pid FROM registry")
            pids = cursor.fetchall()
        new_leader = min(pids)[0]
        self.leader = new_leader
        print(f"[SERVER {self.pid}] Replica {new_leader} becoming the new leader.")
        if new_leader == self.pid:
            self.IS_LEADER = True



# ++++++++++++++  Serve Functions  ++++++++++++++ #
def serve(pid, host):
    """
    Create a communication point for a server for clients to connect to.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_service = ChatService(pid, host)
    chat_pb2_grpc.add_ChatServiceServicer_to_server(chat_service, server)
    server_port = config.BASE_PORT + chat_service.pid
    server.add_insecure_port(f'{host}:{server_port}')
    server.start()
    print(f"[SERVER {chat_service.pid}] Started!")
    chat_service.start_heartbeat()
    try:
        # Use a long sleep loop to keep the main thread alive
        while True:
            time.sleep(86400)  # sleep for 1 day
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping server gracefully...")
        server.stop(0)  # Gracefully shutdown the server



# ++++++++++++++  Main Functions  ++++++++++++++ #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Start the server with a specific PID.")
    parser.add_argument('--pid', type=int, help="The PID of the server to run.  Example: 0", required=True)
    parser.add_argument('--host', type=str, help="4-digit IP host address.  Example: 127.0.0.1", required=True)
    args = parser.parse_args()
    pid = args.pid
    host = args.host
    serve(pid, host)
    