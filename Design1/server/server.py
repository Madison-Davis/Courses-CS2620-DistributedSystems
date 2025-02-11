# server.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import socket
import selectors
import types
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import sqlite3
import logging



# +++++++++++++++ Variables: +++++++++++++++ #
clients = {} # keep track of all clients and their connections subscribed via selector



# ++++++++++++ Database: Set Up ++++++++++++ #
def db_init(connection=None):
    logging.info("SERVER: initializing database")

    # Connect to database, or create if doesn't exist
    db = connection if connection else sqlite3.connect('chat_database.db')

    # Create cursor to interact with database
    cursor = db.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        uuid INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        pwd TEXT NOT NULL,
        logged_in INTEGER NOT NULL CHECK (logged_in IN (0, 1))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        sender TEXT NOT NULL,
        msg TEXT NOT NULL,
        checked INTEGER NOT NULL CHECK (checked IN (0, 1)),
        inbox INTEGER NOT NULL CHECK (inbox IN (0, 1))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drafts (
        draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        recipient TEXT NOT NULL,
        msg TEXT NOT NULL,
        checked INTEGER NOT NULL CHECK (checked IN (0, 1))
    )
    ''')

    db.commit()
    if not connection:
        db.close()


# +++++++++++++++++++  Variables  +++++++++++++++++++ #
sel = selectors.DefaultSelector()



# ++++++++++++ Functions: Processing Requests ++++++++++++ #
def process_request(request, connection=None):
    """Process JSON request from client and return response."""
    try:
        request_json = json.loads(request)
        action = request_json.get("actions", {})

        # Connect to database, or create if doesn't exist
        db = connection if connection else sqlite3.connect('chat_database.db')

        # Create cursor to interact with database
        cursor = db.cursor()

        if "createAccount" in action:
            logging.info("SERVER: starting to create account")
            user = action["createAccount"]["request"]["data"]["username"]
            pwd = action["createAccount"]["request"]["data"]["passwordHash"]
            try:
                # Check that user does not already exist
                cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
                if cursor.fetchone() is not None:
                    logging.info("SERVER: username already exists")
                    response = {
                        "requestId": action["createAccount"]["request"]["requestId"],
                        "status": "error",
                        "msg": "An account with that username already exists.",
                        "data": {}
                    }
                # Are users logged in once they register?
                else:
                    cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", (user, pwd, 1))
                    logging.info("SERVER: account created successfully")
                    response = {
                        "requestId": action["createAccount"]["request"]["requestId"],
                        "status": "ok",
                        "msg": "Account created successfully.",
                        "data": {}
                    }
            except:
                logging.error("SERVER: cannot create account")
                response = {
                    "requestId": action["createAccount"]["request"]["requestId"],
                    "status": "error",
                    "msg": "An account with that username already exists.",
                    "data": {}
                }
        
        elif "login" in action:
            logging.info("SERVER: starting to login")
            user = action["login"]["request"]["data"]["username"]
            pwd = action["login"]["request"]["data"]["passwordHash"]
            try:
                # Check that username and password combo exists
                cursor.execute("SELECT uuid FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
                account = cursor.fetchone()
                if account is not None:
                    cursor.execute("UPDATE accounts SET logged_in = 1 WHERE user = ?", (user,))
                    # Populate data of user
                    # Not newly received messages
                    cursor.execute("""
                        SELECT msg_id, user, sender, msg, checked, inbox
                        FROM messages WHERE user = ? AND inbox = 0
                        ORDER BY msg_id DESC
                    """, (user,))
                    old_messages = cursor.fetchall()
                    logging.info(f"OLD MESSAGES: {old_messages}")
                    old_message_list = [
                        {"msg_id": row[0], "user": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in old_messages
                    ]

                    # Newly received messages in inbox
                    cursor.execute("""
                        SELECT msg_id, user, sender, msg, checked, inbox
                        FROM messages WHERE user = ? AND inbox = 1
                        ORDER BY msg_id DESC
                    """, (user,))
                    new_messages = cursor.fetchall()
                    logging.info(f"NEW MESSAGES: {new_messages}")
                    new_message_list = [
                        {"msg_id": row[0], "user": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in new_messages
                    ]

                    # Saved drafts
                    cursor.execute("""
                        SELECT draft_id, user, recipient, msg, checked
                        FROM drafts
                        WHERE user = ?
                        ORDER BY draft_id
                    """, (user,))
                    drafts = cursor.fetchall()
                    logging.info(f"DRAFTS: {drafts}")
                    draft_list = [
                        {"draft_id": row[0], "user": row[1], "recipient": row[2], "msg": row[3], "checked": row[4]}
                        for row in drafts
                    ]

                    response = {
                        "requestId": action["login"]["request"]["requestId"],
                        "status": "ok",
                        "msg": "Login successful.",
                        "data": {
                            "inboxCount": len(new_message_list),
                            "old_msgs": old_message_list,
                            "inbox_msgs": new_message_list,
                            "drafts": draft_list
                        }
                    }
                    
                    logging.info(f"SERVER: login information {response}")

                else:
                    logging.error("SERVER: 1invalid login credentials")
                    response = {
                        "requestId": action["login"]["request"]["requestId"],
                        "status": "error",
                        "msg": "Invalid credentials.",
                        "data": {}
                    }
            except Exception as e:
                logging.error(f"SERVER: 2invalid login credentials - {str(e)}")
                response = {
                    "requestId": action["login"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Invalid credentials.",
                    "data": {}
                }
        
        elif "getPwd" in action:
            logging.info("SERVER: starting getPwd")
            user = action["getPwd"]["request"]["data"]["username"]
            try:
                # Get password for user
                cursor.execute("SELECT pwd FROM accounts WHERE user = ?", (user,))
                pwd_hash = cursor.fetchone()[0]
                if pwd_hash is None:
                    logging.error("SERVER: getPwd user does not have a pwd")
                    response = {
                        "requestId": action["getPwd"]["request"]["requestId"],
                        "status": "error",
                        "msg": "User does not exist or other error.",
                        "data": {}
                    }
                else:
                    logging.info("SERVER: getPwd user pwd found")
                    response = {
                        "requestId": action["getPwd"]["request"]["requestId"],
                        "status": "ok",
                        "msg": "",
                        "data": {
                            "passwordHash": pwd_hash
                        }
                    }
            except:
                logging.error("SERVER: getPwd user does not have a pwd or other error")
                response = {
                    "requestId": action["getPwd"]["request"]["requestId"],
                    "status": "error",
                    "msg": "User does not exist or other error.",
                    "data": {}
                }
        
        elif "listAccounts" in action:
            logging.info("SERVER: starting listAccounts")
            try:
                # Get all existing usernames
                cursor.execute("SELECT user FROM accounts ORDER BY uuid")
                usernames = [row[0] for row in cursor.fetchall()]
                response = {
                    "requestId": action["listAccounts"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "",
                    "data": {
                        "accounts_users": usernames,
                        "totalCount": len(usernames)
                    }
                }
                logging.info(f"SERVER: listAccounts response {response}")
            except:
                logging.error(f"SERVER: cannot listAccounts")
                response = {
                    "requestId": action["listAccounts"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Not authenticated or other error.",
                    "data": {}
                }
        
        elif "sendMessage" in action:
            logging.info("SERVER: starting sendMessage")
            info = action["sendMessage"]["request"]["data"]
            logging.info(f"send message data: {info}")
            # TODO: Client Outbound Connection
            draft_id = action["sendMessage"]["request"]["data"]["draft_id"]
            user = action["sendMessage"]["request"]["data"]["recipient"]
            sender = action["sendMessage"]["request"]["data"]["sender"]
            msg = action["sendMessage"]["request"]["data"]["content"]
            try:
                # Check if recipient exists
                cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
                if cursor.fetchone() is None:
                    logging.error("SERVER: recipient does not exist")
                    response = {
                        "requestId": action["sendMessage"]["request"]["requestId"],
                        "status": "error",
                        "msg": "Recipient does not exist or other error.",
                        "data": {}
                    }
                else:
                    # Delete draft from sender
                    logging.info("SERVER: deleting draft")
                    cursor.execute("DELETE FROM drafts WHERE draft_id = ?", (draft_id,))
                    # Add message to messages table
                    # Note: `user` is the recipient
                    cursor.execute("""
                        INSERT INTO messages (user, sender, msg, checked, inbox)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user, sender, msg, 0, 1))

                    response = {
                        "requestId": action["sendMessage"]["request"]["requestId"],
                        "status": "ok",
                        "msg": "Message sent (and delivered/stored).",
                        "data": {}
                    }

                    logging.info("SERVER: message delivered to user DB!")
                    logging.info(f"CLIENTS: {clients}")

                    db.commit()

                    # **Immediate Message Delivery**
                    if user in clients:
                        logging.info("SERVER: recipient is online, sending message immediately.")
                        recipient_socket = clients[user]
                        message_data = json.dumps({
                            "action": "receiveMessage",
                            "msgId": draft_id,  # Not actually a draft, but keeps unique ID
                            "user": user,
                            "sender": sender,
                            "msg": msg
                        })
                        recipient_socket.send(message_data.encode('utf-8'))
                        logging.info("SERVER: message sent to recipient's active connection.")
                    
                    # # We updated the user's database, now, can we immediately update inbox?
                    # # Check if recipient is logged in, and if so, send data
                    # cursor.execute("SELECT logged_in FROM accounts WHERE user = ?", (user,))
                    # logged_in = cursor.fetchone()
                    # if user in clients and logged_in:
                    #     recipient_response = {
                    #         "action": "receiveMessage",
                    #         "sender": sender,
                    #         "msg": msg
                    #     }
                    #     client_socket = clients[user]
                    #     message = json.dumps(recipient_response)     # Convert response to JSON
                    #     client_socket.send(message.encode('utf-8'))  # Send the response to the client
                    #     logging.info("SERVER: message sent to user immediately!")
            except:
                logging.info("SERVER: sendMessage recipient does not exist or other error")
                response = {
                    "requestId": action["sendMessage"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Recipient does not exist or other error.",
                    "data": {}
                }
        
        elif "saveDrafts" in action:
            logging.info("SERVER: starting saveDrafts")
            user = action["saveDrafts"]["request"]["data"]["user"]
            drafts = action["saveDrafts"]["request"]["data"]["drafts"]
            try:
                # Reset drafts
                cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
                # Add draft to drafts table
                # Note: `user` is the sender
                logging.info("drafts reset")
                for draft in drafts:
                    recipient = draft["recipient"]
                    msg = draft["msg"]
                    logging.info(f"user {user} recipient {recipient} msg {msg}")
                    cursor.execute("""
                        INSERT INTO drafts (user, recipient, msg, checked)
                        VALUES (?, ?, ?, ?)
                    """, (user, recipient, msg, 0,))
                response = {
                    "requestId": action["saveDrafts"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Draft saved.",
                    "data": {}
                }
                logging.info("SERVER: drafts saved")
            except Exception as e:
                logging.error(f"SERVER: cannot save drafts - {str(e)}")
                response = {
                    "requestId": action["saveDrafts"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Cannot save draft or other error.",
                    "data": {}
                }
        
        elif "addDraft" in action:
            logging.info("SERVER: starting addDraft")
            user = action["addDraft"]["request"]["data"]["user"]
            recipient = action["addDraft"]["request"]["data"]["recipient"]
            msg = action["addDraft"]["request"]["data"]["content"]
            checked = action["addDraft"]["request"]["data"]["checked"]
            try:
                # Add draft to drafts table
                # Note: `user` is the sender
                cursor.execute("""
                    INSERT INTO drafts (user, recipient, msg, checked)
                    VALUES (?, ?, ?, ?) RETURNING draft_id
                """, (user, recipient, msg, checked,))
                response = {
                    "requestId": action["addDraft"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Draft added.",
                    "data": {
                        "draft_id": cursor.fetchone()
                    }
                }
            except Exception as e:
                logging.error(f"SERVER: cannot add draft - {str(e)}")
                response = {
                    "requestId": action["addDraft"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Cannot add draft or other error.",
                    "data": {}
                }
        
        elif "checkMessage" in action:
            logging.info("SERVER: starting checkMessage")
            user = action["checkMessage"]["request"]["data"]["username"]
            msg_id = action["checkMessage"]["request"]["data"]["msgId"]
            try:
                # Update checked status
                cursor.execute("UPDATE messages SET checked = 1 WHERE user = ? AND msg_id = ?", (user, msg_id,))
                logging.info("SERVER: message checked as read")
                response = {
                    "requestId": action["checkMessage"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Message checked as read.",
                    "data": {}
                }
            except:
                logging.error("SERVER: message unable to check as read")
                response = {
                    "requestId": action["checkMessage"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Message unable to read or other error.",
                    "data": {}
                }
        
        elif "downloadMessage" in action:
            logging.info("SERVER: starting downloadMessage")
            user = action["downloadMessage"]["request"]["data"]["username"]
            msg_id = action["downloadMessage"]["request"]["data"]["msgId"]
            try:
                # Update checked status
                cursor.execute("UPDATE messages SET inbox = 0 WHERE user = ? AND msg_id = ?", (user, msg_id,))
                logging.info(f"SERVER: message ID {msg_id} downloaded from inbox")
                response = {
                    "requestId": action["downloadMessage"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Message downloaded from inbox.",
                    "data": {}
                }
            except:
                logging.error("SERVER: message unable to download")
                response = {
                    "requestId": action["downloadMessage"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Message unable to download or other error.",
                    "data": {}
                }
        
        elif "deleteMessage" in action:
            logging.info("SERVER: starting deleteMessage")
            user = action["deleteMessage"]["request"]["data"]["username"]
            msg_id = action["deleteMessage"]["request"]["data"]["msgId"]
            try:
                # Remove message from messages table
                cursor.execute("DELETE FROM messages WHERE user = ? AND msg_id = ?", (user, msg_id,))
                logging.info("SERVER: message deleted")
                response = {
                    "requestId": action["deleteMessage"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Message deleted.",
                    "data": {}
                }
            except:
                logging.error("SERVER: cannot delete message")
                response = {
                    "requestId": action["deleteMessage"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Not authorized to delete or other error.",
                    "data": {}
                }
        
        elif "deleteAccount" in action:
            logging.info("SERVER: starting deleteAccount")
            user = action["deleteAccount"]["request"]["data"]["username"]
            pwd = action["deleteAccount"]["request"]["data"]["passwordHash"]
            try:
                # Remove messages sent to the user, user's drafts, and user's account information
                cursor.execute("DELETE FROM messages WHERE user = ?", (user,))
                cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
                cursor.execute("DELETE FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
                logging.info("SERVER: account, messages, drafts deleted")
                response = {
                    "requestId": action["deleteAccount"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Account and all messages have been deleted.",
                    "data": {}
                }
            except:
                logging.info("SERVER: error with deleting account")
                response = {
                    "requestId": action["deleteAccount"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Invalid credentials or other error.",
                    "data": {}
                }
        
        elif "logout" in action:
            logging.info("SERVER: starting logout")
            user = action["logout"]["request"]["data"]["username"]
            try:
                # Update logged in status
                cursor.execute("UPDATE accounts SET logged_in = 0 WHERE user = ?", (user,))
                logging.info("SERVER: successfully logged out")
                response = {
                    "requestId": action["logout"]["request"]["requestId"],
                    "status": "ok",
                    "msg": "Logged out successfully.",
                    "data": {}
                }

                # Remove user from active clients
                if user in clients:
                    del clients[user]
                    logging.info(f"SERVER: {user} removed from active clients.")
            except:
                logging.error("SERVER; error logging out")
                response = {
                    "requestId": action["logout"]["request"]["requestId"],
                    "status": "error",
                    "msg": "Not logged in or other error.",
                    "data": {}
                }
        
        else:
            logging.error("SERVER: UNKNOWN ERROR")
            response = {
                "status": "error",
                "msg": "Unknown error occurred.",
                "data": {}
            }
        
        db.commit()
        if not connection:
            db.close()
        return json.dumps(response).encode("utf-8")
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON"}).encode("utf-8")





# ++++++++++ Main Functions: Handling Connections ++++++++++ #
def accept_wrapper(sock):
    """Accept connection from client."""
    conn, addr = sock.accept()
    logging.info(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # inb   = in buffer, starts out empty
    # outb  = out buffer, starts out empty
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    # clients[addr] = conn

def service_connection(key, mask):
    """Accept connection from client."""
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(4096)
        if recv_data:
            logging.info(f"Raw received data: {recv_data}")
            data.outb += recv_data
        else:
            logging.info(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    # If client requests for us to do a task:
        # decode task
        # process task
        # format response into JSON
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            try:
                # Split multiple JSON objects if received in one buffer
                requests = data.outb.decode("utf-8").strip().split("}{")
                for i in range(len(requests)):
                    if i > 0:
                        requests[i] = "{" + requests[i]  # Fix missing curly brace
                    if i < len(requests) - 1:
                        requests[i] += "}"  # Fix missing curly brace
                
                for request_json in requests:
                    logging.info(f"Processing request: {request_json}")
                    try:
                        actions = json.loads(request_json).get("actions", {})
                        # If this is a login request, store the socket with the username
                        if "login" in actions:
                            username = actions["login"]["request"]["data"]["username"]
                            clients[username] = sock  # Store socket by username
                            logging.info(f"SERVER: {username} logged in and added to active clients.")
                        return_data = process_request(request_json)
                        sock.send(return_data)
                    except Exception as e:
                        logging.error(f"Error processing request: {e}")
                
                data.outb = b""  # Clear buffer after processing all messages
            except Exception as e:
                logging.error(f"Error handling request: {e}")

def start_server():
    db_init()
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((config.HOST, config.PORT))
    lsock.listen()
    print("Listening on", (config.HOST, config.PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        print("Closing server...")
        sel.close()
        lsock.close()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,  # Change to logging.INFO to reduce verbosity
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("server.log"),  # Save logs to a file
            logging.StreamHandler()  # Show logs in the console
        ]
    )
    # Start server
    start_server()
