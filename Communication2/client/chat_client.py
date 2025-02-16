import grpc
from comm import chat_pb2
from comm import chat_pb2_grpc

class ChatClient:
    def __init__(self, server_address='localhost:50051'):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
    
    def create_account(self, username, password_hash):
        request = chat_pb2.CreateAccountRequest(username=username, password_hash=password_hash)
        response = self.stub.CreateAccount(request)
        return response.success, response.message
    
    def login(self, username, password_hash):
        request = chat_pb2.LoginRequest(username=username, password_hash=password_hash)
        response = self.stub.Login(request)
        return response.success, response.message, response.inbox_count, response.old_messages, response.inbox_messages, response.drafts
    
    def send_message(self, draft_id, recipient, sender, content):
        request = chat_pb2.SendMessageRequest(draft_id=draft_id, recipient=recipient, sender=sender, content=content)
        response = self.stub.SendMessage(request)
        return response.msg_id
    
    def download_message(self, username, msg_id):
        request = chat_pb2.DownloadMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.DownloadMessage(request)
        return response.msg_id
    
    def check_message(self, username, msg_id):
        request = chat_pb2.CheckMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.CheckMessage(request)
        return response.success, response.message
    
    def delete_message(self, username, msg_id):
        request = chat_pb2.DeleteMessageRequest(username=username, msg_id=msg_id)
        response = self.stub.DeleteMessage(request)
        return response.success, response.message
    
    def add_draft(self, username, recipient, message, checked):
        request = chat_pb2.AddDraftRequest(username=username, recipient=recipient, message=message, checked=checked)
        response = self.stub.AddDraft(request)
        return response.draft_id
    
    def save_drafts(self, username, drafts):
        request = chat_pb2.SaveDraftsRequest(username=username, drafts=drafts)
        response = self.stub.SaveDrafts(request)
        return response.success, response.message
    
    def logout(self, username):
        request = chat_pb2.LogoutRequest(username=username)
        response = self.stub.Logout(request)
        return response.success, response.message
    
    def list_accounts(self):
        request = chat_pb2.ListAccountsRequest()
        response = self.stub.ListAccounts(request)
        return response.usernames
    
    def delete_account(self):
        request = chat_pb2.DeleteAccountRequest()
        response = self.stub.DeleteAccount(request)
        return response.success, response.message
    
    def get_password(self, username):
        request = chat_pb2.GetPasswordRequest(username=username)
        response = self.stub.GetPassword(request)
        return response.password_hash
    
    def receive_messages(self, callback):
        request = chat_pb2.ReceiveMessageRequest()
        for message in self.stub.ReceiveMessageStream(request):
            callback(message)