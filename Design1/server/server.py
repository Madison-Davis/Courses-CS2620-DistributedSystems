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



# ++++++++++++ Database: Set Up ++++++++++++ #
def db_init(connection=None):
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
            user = action["createAccount"]["request"]["data"]["username"]
            pwd = action["createAccount"]["request"]["data"]["passwordHash"]
            try:
                # Check that user does not already exist
                cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
                if cursor.fetchone() is not None:
                    logging.debug("username already exists")
                    response = action["createAccount"]["errorResponse"]
                # Are users logged in once they register?
                else:
                    logging.debug("creating new account")
                    cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", (user, pwd, 1))
                    response = action["createAccount"]["successResponse"]
            except:
                response = action["createAccount"]["errorResponse"]
        
        elif "login" in action:
            user = action["login"]["request"]["data"]["username"]
            pwd = action["login"]["request"]["data"]["passwordHash"]
            try:
                # Check that username and password combo exists
                cursor.execute("SELECT uuid FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
                account = cursor.fetchone()
                if account is not None:
                    cursor.execute("UPDATE accounts SET logged_in = 1 WHERE user = ?", (user,))
                    response = action["login"]["successResponse"]
                    # Populate data of user
                    # Not newly received messages
                    cursor.execute("""
                        SELECT msg_id, user, sender, msg, checked, inbox
                        FROM messages WHERE user = ? AND inbox = 0
                        ORDER BY msg_id DESC
                    """, (user,))
                    old_messages = cursor.fetchall()
                    old_message_list = [
                        {"msg_id": row[0], "user": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in old_messages
                    ]
                    response["data"]["old_msgs"] = old_message_list

                    # Newly received messages in inbox
                    cursor.execute("""
                        SELECT msg_id, user, sender, msg, checked, inbox
                        FROM messages WHERE user = ? AND inbox = 1
                        ORDER BY msg_id DESC
                    """, (user,))
                    new_messages = cursor.fetchall()
                    new_message_list = [
                        {"msg_id": row[0], "user": row[1], "sender": row[2],
                        "msg": row[3], "checked": row[4], "inbox": row[5]}
                        for row in new_messages
                    ]
                    response["data"]["new_msgs"] = new_message_list
                    response["data"]["inboxCount"] = len(new_message_list)

                    # Saved drafts
                    cursor.execute("""
                        SELECT draft_id, user, recipient, msg
                        FROM drafts
                        WHERE user = ?
                        ORDER BY draft_id
                    """, (user,))
                    drafts = cursor.fetchall()
                    draft_list = [
                        {"draft_id": row[0], "user": row[1], "recipient": row[2], "msg": row[3], "checked": row[4]}
                        for row in drafts
                    ]
                    response["data"]["drafts"] = draft_list

                else:
                    response = action["login"]["errorResponse"]
            except:
                response = action["login"]["errorResponse"]
        
        elif "getPwd" in action:
            user = action["getPwd"]["request"]["data"]["username"]
            try:
                # Get password for user
                cursor.execute("SELECT pwd FROM accounts WHERE user = ?", (user,))
                pwd_hash = cursor.fetchone()[0]
                response = action["getPwd"]["successResponse"]
                response["data"]["passwordHash"] = pwd_hash
            except:
                response = action["getPwd"]["errorResponse"]
        
        elif "listAccounts" in action:
            try:
                # Get all existing usernames
                cursor.execute("SELECT user FROM accounts ORDER BY uuid")
                usernames = [row[0] for row in cursor.fetchall()]
                response = action["listAccounts"]["successResponse"]
                response["data"]["accounts_users"] = usernames
                response["data"]["totalCount"] = len(usernames)
            except:
                response = action["listAccounts"]["errorResponse"]
        
        elif "sendMessage" in action:
            # TODO: Client Outbound Connection
            user = action["sendMessage"]["request"]["data"]["user"]
            sender = action["sendMessage"]["request"]["data"]["sender"]
            msg = action["sendMessage"]["request"]["data"]["content"]
            try:
                # Check if recipient exists
                cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
                if cursor.fetchone() is None:
                    response = action["sendMessage"]["errorResponse"]
                else:
                    # Add message to messages table
                    # Note: `user` is the recipient
                    cursor.execute("""
                        INSERT INTO messages (user, sender, msg, checked, inbox)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sender, user, msg, 0, 1))
                    response = action["sendMessage"]["successResponse"]
            except:
                response = action["sendMessage"]["errorResponse"]
        
        elif "saveDrafts" in action:
            user = action["saveDrafts"]["request"]["data"]["user"]
            drafts = action["saveDrafts"]["request"]["data"]["drafts"]
            try:
                # Reset drafts
                cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
                # Add draft to drafts table
                # Note: `user` is the sender
                for recipient, msg in drafts:
                    cursor.execute("""
                        INSERT INTO drafts (user, recipient, msg, checked)
                        VALUES (?, ?, ?, ?)
                    """, (user, recipient, msg, 0))
                response = action["saveDraft"]["successResponse"]
            except:
                response = action["saveDraft"]["errorResponse"]
        
        elif "checkMessage" in action:
            user = action["checkMessage"]["request"]["data"]["username"]
            msg_id = action["checkMessage"]["request"]["data"]["msgId"]
            try:
                # Update checked status
                cursor.execute("UPDATE messages SET checked = 1 WHERE user = ? AND msg_id = ?", (user, msg_id,))
                response = action["checkMessage"]["successResponse"]
            except:
                response = action["checkMessage"]["errorResponse"]
        
        elif "downloadMessage" in action:
            user = action["downloadMessage"]["request"]["data"]["username"]
            msg_id = action["downloadMessage"]["request"]["data"]["msgId"]
            try:
                # Update checked status
                cursor.execute("UPDATE messages SET inbox = 0 WHERE user = ? AND msg_id = ?", (user, msg_id,))
                response = action["downloadMessage"]["successResponse"]
            except:
                response = action["downloadMessage"]["errorResponse"]
        
        elif "deleteMessage" in action:
            user = action["deleteMessage"]["request"]["data"]["username"]
            msg_id = action["deleteMessage"]["request"]["data"]["msgId"]
            try:
                # Remove message from messages table
                cursor.execute("DELETE FROM messages WHERE user = ? AND msg_id = ?", (user, msg_id,))
                response = action["deleteMessage"]["successResponse"]
            except:
                response = action["deleteMessage"]["errorResponse"]
        
        elif "deleteAccount" in action:
            user = action["deleteAccount"]["request"]["data"]["username"]
            pwd = action["deleteAccount"]["request"]["data"]["passwordHash"]
            try:
                # Remove messages sent to the user, user's drafts, and user's account information
                cursor.execute("DELETE FROM messages WHERE user = ?", (user,))
                cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
                cursor.execute("DELETE FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
                response = action["deleteAccount"]["successResponse"]
            except:
                response = action["deleteAccount"]["errorResponse"]
        
        elif "logout" in action:
            user = action["logout"]["request"]["data"]["username"]
            try:
                # Update logged in status
                cursor.execute("UPDATE accounts SET logged_in = 0 WHERE user = ?", (user,))
                response = action["logout"]["successResponse"]
            except:
                response = action["logout"]["errorResponse"]
        
        else:
            response = {
                "status": "error",
                "msg": "Unknown error occurred.",
                "data": {}
            }
        
        db.commit()
        if not connection:
            db.close()
        logging.info("reached end of process_request")
        logging.info(f"response: {response}")
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

def service_connection(key, mask):
    """Accept connection from client."""
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(config.PORT)
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
                request_json = data.outb.decode("utf-8").strip()
                return_data = process_request(request_json)
                sent = sock.send(return_data)
                data.outb = data.outb[sent:]
            except Exception as e:
                logging.error(f"Error processing request: {e}")

def start_server():
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

    start_server()
