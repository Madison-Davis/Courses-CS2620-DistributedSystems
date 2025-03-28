# chat_client.py



# +++++++++++++ Imports and Installs +++++++++++++ #
import grpc
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from comm import chat_pb2
from comm import chat_pb2_grpc
from config import config



# ++++++++++++++  Class Definition  ++++++++++++++ #
class ChatClient:
    def __init__(self, server_address=None):
        """
        Establish channel and service stub.
        """
        # for testing purposes, one can set arbitrarily the server address
        # otherwise, simply find the leader by calling get_leader
        # leader_pid will help when needing to find a new leader via incrementing
        if server_address is not None:
            self.leader_pid = int(server_address[-5:])-config.BASE_PORT
            leader_address = server_address
        else:
            self.leader_pid = None
            leader_address = self.get_leader()
        self.channel = grpc.insecure_channel(leader_address)
        print(f"Connected to address {leader_address}")
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
    
    def create_account(self, username, password_hash):
        """
        Create new user account
        Return: success (T/F)
        """
        request = chat_pb2.CreateAccountRequest(username=username, password_hash=password_hash)
        try:
            response = self.stub.CreateAccount(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.create_account(username, password_hash)
            raise
    
    def login(self, username, password_hash):
        """
        Login existing user
        Return: inbox count, list of old messages, list of inbox messages, list of drafts
        """
        request = chat_pb2.LoginRequest(username=username, password_hash=password_hash)
        try:
            response = self.stub.Login(request)
            return response.inbox_count, response.old_messages, response.inbox_messages, response.drafts
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.login(username, password_hash)
            raise
    
    def send_message(self, draft_id, recipient, sender, content):
        """
        Send message to recipient
        Return: newly created message ID
        """
        request = chat_pb2.SendMessageRequest(draft_id=draft_id, recipient=recipient, sender=sender, content=content)
        try:
            response = self.stub.SendMessage(request)
            return response.msg_id
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.send_message(draft_id, recipient, sender, content)
            raise
    
    def download_message(self, username, msg_id):
        """
        Download message from inbox
        Return: success (T/F)
        """
        request = chat_pb2.DownloadMessageRequest(username=username, msg_id=msg_id)
        try:
            response = self.stub.DownloadMessage(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.download_message(username, msg_id)
            raise
    
    def check_message(self, username, msg_id):
        """
        Check message as read
        Return: success (T/F)
        """
        request = chat_pb2.CheckMessageRequest(username=username, msg_id=msg_id)
        try:
            response = self.stub.CheckMessage(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.check_message(username, msg_id)
            raise
    
    def delete_message(self, username, msg_id):
        """
        Delete message from storage and GUI
        Return: success (T/F)
        """
        request = chat_pb2.DeleteMessageRequest(username=username, msg_id=msg_id)
        try:
            response = self.stub.DeleteMessage(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.delete_message(username, msg_id)
            raise
    
    def add_draft(self, username, recipient, message, checked):
        """
        Add new draft to database
        Return: newly created draft ID
        """
        request = chat_pb2.AddDraftRequest(username=username, recipient=recipient, message=message, checked=checked)
        try:
            response = self.stub.AddDraft(request)
            return response.draft_id
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.add_draft(username, recipient, message, checked)
            raise
    
    def save_drafts(self, username, drafts):
        """
        Save draft status in database
        Return: success (T/F)
        """
        request = chat_pb2.SaveDraftsRequest(username=username, drafts=drafts)
        try:
            response = self.stub.SaveDrafts(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.save_drafts(username, drafts)
            raise
    
    def logout(self, username):
        """
        Log user out of current session
        Return: success (T/F)
        """
        request = chat_pb2.LogoutRequest(username=username)
        try:
            response = self.stub.Logout(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.logout(username)
            raise
    
    def list_accounts(self):
        """
        List all existing accounts
        Return: list of usernames
        """
        request = chat_pb2.ListAccountsRequest()
        try:
            response = self.stub.ListAccounts(request)
            return response.usernames
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.list_accounts()
            raise
    
    def delete_account(self, username):
        """
        Delete account from application
        Return: success (T/F)
        """
        request = chat_pb2.DeleteAccountRequest(username=username)
        try:
            response = self.stub.DeleteAccount(request)
            return response.success
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.delete_account(username)
            raise
    
    def get_password(self, username):
        """
        Get password hash from database to compare
        Return: password hash
        """
        request = chat_pb2.GetPasswordRequest(username=username)
        try:
            response = self.stub.GetPassword(request)
            return response.password_hash
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    return self.get_password(username)
            raise

    def receive_messages(self, user, callback):
        """
        Listen for incoming live messages and update GUI inbox count
        Return: None
        """
        print("Listening for messages...")
        try:
            for response in self.stub.ReceiveMessageStream(chat_pb2.ReceiveMessageRequest(username=user)):
                print(f"[{response.msg_id}] {response.sender} → {response.username}: {response.msg}")
                print(f"Inbox Count: {response.inbox_count}\n")          
                message = chat_pb2.Message(
                    msg_id = response.msg_id,
                    username = response.username,
                    sender = response.sender,
                    msg = response.msg,
                    checked = 0,
                    inbox = 1
                )

                callback(message)
        except grpc.RpcError as e:
            # Try again if disconnected from server
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                print("[CLIENT] Connection failed. Attempting to reconnect to new leader...")
                if self.reconnect():
                    # Restart message stream
                    self.receive_messages(user, callback)
                    return
            raise

    def reconnect(self):
        """Fetch the new leader's address and reinitialize the connection."""
        new_leader = self.get_leader()
        if new_leader:
            print(f"[CLIENT] New leader found: {new_leader}.  Reconnecting...")
            # Update channel and stub with the new leader address.
            self.channel = grpc.insecure_channel(new_leader)
            print(f"Connecting to address {new_leader}")
            self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
            return True
        else:
            print("[CLIENT] Could not get the new leader. Please try again later.")
            return False

    def get_leader(self):
        """
        Contact a known peer (or the current leader) to fetch the current leader's address.
        """
        # Determine where to begin looking for range of leaders
        # If first-time, start at 0
        # If new leader, it will be > old leader's pid
        p = 0
        if self.leader_pid is not None:
            p = self.leader_pid
        while p < config.MAX_PID:
            print(f"[CLIENT] Contacting With PID: {p}")
            for host in config.ALL_HOSTS:
                addr = f"{host}:{config.BASE_PORT+p}"
                print(f"[CLIENT] Contacting Addr: {addr}")
                
                # Ask potentially alive server who is the leader
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = chat_pb2_grpc.ChatServiceStub(channel)
                        request = chat_pb2.GetLeaderRequest()
                        response = stub.GetLeader(request, timeout=2)
                        if response.success and response.leader_address:
                            print(f"[CLIENT] Reported leader: {response.leader_address}")
                            self.leader_pid = p
                            return response.leader_address
                
                # If they do not respond, likely not alive, continue
                except Exception as e:
                    continue
            p += 1
        return None


    
