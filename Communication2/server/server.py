import grpc
from concurrent import futures
from comm import chat_pb2
from comm import chat_pb2_grpc
import sqlite3
import logging
from config import config

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.db_connection = sqlite3.connect('chat_database.db', check_same_thread=False)
        self.cursor = self.db_connection.cursor()

        # Create tables
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            uuid INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            pwd TEXT NOT NULL,
            logged_in INTEGER NOT NULL CHECK (logged_in IN (0, 1))
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            sender TEXT NOT NULL,
            msg TEXT NOT NULL,
            checked INTEGER NOT NULL CHECK (checked IN (0, 1)),
            inbox INTEGER NOT NULL CHECK (inbox IN (0, 1))
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            recipient TEXT NOT NULL,
            msg TEXT NOT NULL,
            checked INTEGER NOT NULL CHECK (checked IN (0, 1))
        )
        ''')

        self.db_connection.commit()

    def CreateAccount(self, request, context):
        """
        Creates account for new user.
        Return: GenericResponse (success, message)
        """
        username = request.username
        password_hash = request.password_hash
        
        try:
            self.cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (username,))
            if self.cursor.fetchone() is not None:
                return chat_pb2.GenericResponse(success=False, message="Username already exists")
            
            self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, 1)", (username, password_hash))
            self.db_connection.commit()
            return chat_pb2.GenericResponse(success=True, message="Account created successfully")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Create account error")
    
    def Login(self, request, context):
        """
        Marks user as logged in, fetches account information.
        Return: LoginResponse (success, message, inbox count, old messages, new messages, drafts)
        """
        username = request.username
        password_hash = request.password_hash
        
        try:
            self.cursor.execute("SELECT uuid FROM accounts WHERE user = ? AND pwd = ?", (username, password_hash))
            account = self.cursor.fetchone()
            if account is not None:
                self.cursor.execute("UPDATE accounts SET logged_in = 1 WHERE user = ?", (username,))

                # Populate data of user
                # Not newly received messages
                self.cursor.execute("""
                    SELECT msg_id, user, sender, msg, checked, inbox
                    FROM messages WHERE user = ? AND inbox = 0
                    ORDER BY msg_id DESC
                """, (username,))
                old_messages = self.cursor.fetchall()

                old_message_list = [
                    {"msg_id": row[0], "user": row[1], "sender": row[2],
                    "msg": row[3], "checked": row[4], "inbox": row[5]}
                    for row in old_messages
                ]

                # Newly received messages in inbox
                self.cursor.execute("""
                    SELECT msg_id, user, sender, msg, checked, inbox
                    FROM messages WHERE user = ? AND inbox = 1
                    ORDER BY msg_id DESC
                """, (username,))
                new_messages = self.cursor.fetchall()

                new_message_list = [
                    {"msg_id": row[0], "user": row[1], "sender": row[2],
                    "msg": row[3], "checked": row[4], "inbox": row[5]}
                    for row in new_messages
                ]

                # Saved drafts
                self.cursor.execute("""
                    SELECT draft_id, user, recipient, msg, checked
                    FROM drafts
                    WHERE user = ?
                    ORDER BY draft_id
                """, (username,))
                drafts = self.cursor.fetchall()

                draft_list = [
                    {"draft_id": row[0], "user": row[1], "recipient": row[2], "msg": row[3], "checked": row[4]}
                    for row in drafts
                ]
                chat_pb2.LoginResponse(success=True, message="Login successful", inbox_count=len(new_message_list), old_messages=old_message_list, inbox_messages=new_message_list, drafts=draft_list)
                
                self.cursor.execute("UPDATE accounts SET logged_in = 1 WHERE user = ?", (username,))
                self.db_connection.commit()
            
            else:
                return chat_pb2.LoginResponse(success=False, message="Invalid credentials")
        except Exception as e:
            return chat_pb2.LoginResponse(success=False, message="Login error")
    
    def GetPassword(self, request, context):
        """
        Checks if user exists, and if so, returns password hash.
        Return: GetPasswordResponse (success, message, pwd_hash)
        """
        username = request.username

        try:
            self.cursor.execute("SELECT pwd FROM accounts WHERE user = ?", (username,))
            pwd_hash = self.cursor.fetchone()[0]
            if pwd_hash is None:
                return chat_pb2.GetPasswordResponse(success=False, message="User does not exist")
            else:
                return chat_pb2.GetPasswordResponse(success=True, message="Password found", password_hash=pwd_hash)
        except Exception as e:
            return chat_pb2.GetPasswordResponse(success=False, message="Get password error")
    
    def SendMessage(self, request, context):
        """
        Check if recipient exists, delete draft, add message
        Return: message ID of newly sent message
        """
        draft_id = request.draft_id
        recipient = request.recipient
        sender = request.sender
        content = request.content

        try:
            # Check if recipient exists
            self.cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (recipient,))
            if self.cursor.fetchone() is None:
                return chat_pb2.SendMessageResponse(success=False, message="Recipient does not exist")
            
            # Delete draft from sender
            self.cursor.execute("DELETE FROM drafts WHERE draft_id = ?", (draft_id,))

            # Add message to messages table
            self.cursor.execute("""
                INSERT INTO messages (user, sender, msg, checked, inbox)
                VALUES (?, ?, ?, ?, ?) RETURNING msg_id
            """, (recipient, sender, content, 0, 1))
            msg_id = self.cursor.fetchone()
            self.db_connection.commit()

            ### OMMITTED IMMEDIATE MESSAGE DELIVERY
            
            return chat_pb2.SendMessageResponse(success=True, message="Message sent", msg_id=msg_id[0])
        except Exception as e:
            return chat_pb2.SendMessageResponse(success=False, message="Send message error")

    def ListAccounts(self, request, context):
        """
        Fetches all existing usernames.
        Return: list of account usernames
        """
        try:
            self.cursor.execute("SELECT user FROM accounts ORDER BY uuid")
            usernames = [row[0] for row in self.cursor.fetchall()]
            return chat_pb2.ListAccountsResponse(success=True, message="Accounts fetched", usernames=usernames)
        except Exception as e:
            return chat_pb2.ListAccountsResponse(success=False, message="Could not fetch accounts")
    
    def SaveDrafts(self, request, context):
        """
        Saves drafts of user to updated status.
        Return: GenericResponse (success, message)
        """
        username = request.username
        drafts = request.drafts

        try:
            # Reset drafts
            self.cursor.execute("DELETE FROM drafts WHERE user = ?", (username,))

            # Add draft to drafts table
            # Note: `user` is the sender
            # Assumes that drafts is a list of dictionaries
            for draft in drafts:
                recipient = draft["recipient"]
                msg = draft["msg"]
                self.cursor.execute("""
                    INSERT INTO drafts (user, recipient, msg, checked)
                    VALUES (?, ?, ?, ?)
                """, (username, recipient, msg, 0,))
            self.db_connection.commit()
            
            return chat_pb2.GenericResponse(success=True, message="Draft saved")
        except Exception as e:
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
            # Note: `user` is the sender
            self.cursor.execute("""
                INSERT INTO drafts (user, recipient, msg, checked)
                VALUES (?, ?, ?, ?) RETURNING draft_id
            """, (username, recipient, msg, checked,))
            self.db_connection.commit()
            return chat_pb2.AddDraftResponse(success=True, message="Draft added", draft_id=self.cursor.fetchone()[0])
        except Exception as e:
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
            self.cursor.execute("UPDATE messages SET checked = 1 WHERE user = ? AND msg_id = ?", (username, msg_id,))
            self.db_connection.commit()
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
            self.cursor.execute("UPDATE messages SET inbox = 0 WHERE user = ? AND msg_id = ?", (username, msg_id,))
            self.db_connection.commit()
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
            self.cursor.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
            self.db_connection.commit()
            return chat_pb2.GenericResponse(success=True, message="Message deleted")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Message unable to delete")
    
    def DeleteAccount(self, request, context):
        """
        Delete account from database
        Return: GenericResponse (success, message)
        """
        username = request.username

        try:
            # Remove messages sent to the user, user's drafts, and user's account information
            self.cursor.execute("DELETE FROM messages WHERE user = ?", (username,))
            self.cursor.execute("DELETE FROM drafts WHERE user = ?", (username,))
            self.cursor.execute("DELETE FROM accounts WHERE user = ?", (username,))
            self.db_connection.commit()
            return chat_pb2.GenericResponse(success=True, message="Account and all messages deleted")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Unable to delete account")
    
    def Logout(self, request, context):
        """
        Set user as logged out
        Return: GenericResponse (success, message)
        """
        username = request.username

        try:
            self.cursor.execute("UPDATE accounts SET logged_in = 0 WHERE user = ?", (username,))
            self.db_connection.commit()
            return chat_pb2.GenericResponse(success=True, message="Logged out successfully")
        except Exception as e:
            return chat_pb2.GenericResponse(success=False, message="Unable to log out")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f'[::]:{config.PORT}')
    server.start()
    logging.info(f"Server started on port {config.PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
