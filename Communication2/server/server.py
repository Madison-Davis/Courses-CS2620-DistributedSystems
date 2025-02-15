import grpc
from concurrent import futures
from comm import chat_pb2
from comm import chat_pb2_grpc
import sqlite3
import logging

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.db_connection = sqlite3.connect('chat_database.db', check_same_thread=False)
        self.cursor = self.db_connection.cursor()

    def CreateAccount(self, request, context):
        username = request.username
        password_hash = request.password_hash
        
        self.cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (username,))
        if self.cursor.fetchone():
            return chat_pb2.GenericResponse(success=False, message="Username already exists")
        
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, 1)", (username, password_hash))
        self.db_connection.commit()
        return chat_pb2.GenericResponse(success=True, message="Account created successfully")
    
    def Login(self, request, context):
        username = request.username
        password_hash = request.password_hash
        
        self.cursor.execute("SELECT uuid FROM accounts WHERE user = ? AND pwd = ?", (username, password_hash))
        account = self.cursor.fetchone()
        if not account:
            return chat_pb2.LoginResponse(success=False, message="Invalid credentials")
        
        self.cursor.execute("UPDATE accounts SET logged_in = 1 WHERE user = ?", (username,))
        self.db_connection.commit()
        
        return chat_pb2.LoginResponse(success=True, message="Login successful", inbox_count=0, old_messages=[], inbox_messages=[], drafts=[])
    
    def SendMessage(self, request, context):
        recipient = request.recipient
        sender = request.sender
        content = request.content
        
        self.cursor.execute("INSERT INTO messages (user, sender, msg, checked, inbox) VALUES (?, ?, ?, 0, 1) RETURNING msg_id", (recipient, sender, content))
        msg_id = self.cursor.fetchone()[0]
        self.db_connection.commit()
        
        return chat_pb2.SendMessageResponse(msg_id=msg_id)

    def ListAccounts(self, request, context):
        self.cursor.execute("SELECT user FROM accounts ORDER BY uuid")
        usernames = [row[0] for row in self.cursor.fetchall()]
        return chat_pb2.ListAccountsResponse(usernames=usernames)

    def Logout(self, request, context):
        username = request.username
        self.cursor.execute("UPDATE accounts SET logged_in = 0 WHERE user = ?", (username,))
        self.db_connection.commit()
        return chat_pb2.GenericResponse(success=True, message="Logged out successfully")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("Server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
