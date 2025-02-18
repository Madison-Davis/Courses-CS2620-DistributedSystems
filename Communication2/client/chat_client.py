import grpc
import os
import sys
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from comm import chat_pb2
from comm import chat_pb2_grpc
from config import config


class ChatClient:
    def __init__(self, server_address=f'localhost:{config.PORT}'):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
    
    def create_account(self, username, password_hash):
        request = chat_pb2.CreateAccountRequest(username=username, password_hash=password_hash)
        response = self.stub.CreateAccount(request)
        return response.success
    
    def login(self, username, password_hash):
        request = chat_pb2.LoginRequest(username=username, password_hash=password_hash)
        response = self.stub.Login(request)
        return response.inbox_count, response.old_messages, response.inbox_messages, response.drafts
    
    def send_message(self, draft_id, recipient, sender, content):
        request = chat_pb2.SendMessageRequest(draft_id=draft_id, recipient=recipient, sender=sender, content=content)
        response = self.stub.SendMessage(request)
        return response.msg_id
    
    def download_message(self, username, msg_id):
        request = chat_pb2.DownloadMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.DownloadMessage(request)
        return response.success
    
    def check_message(self, username, msg_id):
        request = chat_pb2.CheckMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.CheckMessage(request)
        return response.success
    
    def delete_message(self, username, msg_id):
        request = chat_pb2.DeleteMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.DeleteMessage(request)
        return response.success
    
    def add_draft(self, username, recipient, message, checked):
        request = chat_pb2.AddDraftRequest(username=username, recipient=recipient, message=message, checked=checked)
        response = self.stub.AddDraft(request)
        return response.draft_id
    
    def save_drafts(self, username, drafts):
        request = chat_pb2.SaveDraftsRequest(username=username, drafts=drafts)
        response = self.stub.SaveDrafts(request)
        return response.success
    
    def logout(self, username):
        request = chat_pb2.LogoutRequest(username=username)
        response = self.stub.Logout(request)
        return response.success
    
    def list_accounts(self):
        request = chat_pb2.ListAccountsRequest()
        response = self.stub.ListAccounts(request)
        return response.usernames
    
    def delete_account(self, username):
        request = chat_pb2.DeleteAccountRequest(username=username)
        response = self.stub.DeleteAccount(request)
        return response.success
    
    def get_password(self, username):
        request = chat_pb2.GetPasswordRequest(username=username)
        response = self.stub.GetPassword(request)
        return response.password_hash
    
    async def receive_messages(self, callback, username):
        """Listens for incoming messages from the server and updates GUI."""
        request = chat_pb2.ReceiveMessageRequest(username=username)

        print(f"[CLIENT] Listening for incoming messages for {username}...")
        
        while True:  # Keep the stream open indefinitely
            try:
                async for message in self.stub.ReceiveMessageStream(request):
                    print(f"[CLIENT] Received live message from {message.sender}: {message.msg} (Inbox: {message.inbox_count})")
                    callback(message)  # Call GUI update function
            except grpc.RpcError as e:
                print(f"[CLIENT] ERROR: Stream closed unexpectedly. Reconnecting in 3 seconds... ({e})")
                await asyncio.sleep(3)  # Wait before retrying