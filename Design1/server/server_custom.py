import sys
import os
import socket
import selectors
import struct
import types
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

def process_request(message_type, payload, connection=None):
    try:
        # Connect to database, or create if doesn't exist
        db = connection if connection else sqlite3.connect('chat_database.db')
        # Create cursor to interact with database
        cursor = db.cursor()

        response_payload = "error"
        if message_type == 0x0003:  # Create Account
            user, pwd = payload.split(":")
            cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
            if cursor.fetchone() is not None:
                response_payload = "error:exists"
            else:
                cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, 1)", (user, pwd))
                response_payload = "ok"
        
        elif message_type == 0x0001:  # Login
            user, pwd = payload.split(":")
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
                old_msgs_list = [
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
                inbox_msgs_list = [
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
                drafts_list = [
                    {"draft_id": row[0], "user": row[1], "recipient": row[2], "msg": row[3], "checked": row[4]}
                    for row in drafts
                ]

                inboxCount = len(inbox_msgs_list)
                response_payload = f"[{inboxCount},{old_msgs_list},{inbox_msgs_list},{drafts_list}]"
            else:
                response_payload = "error:invalid"
        
        elif message_type == 0x0004:  # List Accounts
            cursor.execute("SELECT user FROM accounts ORDER BY uuid")
            usernames = [row[0] for row in cursor.fetchall()]
            response_payload = f"{len(usernames)}:" + ",".join(usernames)
        
        elif message_type == 0x0005:  # Get Password
            cursor.execute("SELECT pwd FROM accounts WHERE user = ?", (payload,))
            pwd_hash = cursor.fetchone()[0]
            if pwd_hash is None:
                response_payload = "error:exist"
            else:
                response_payload = pwd_hash
        
        elif message_type == 0x0002:  # Send Message
            draft_id, user, sender, content = payload.split(":")
            cursor.execute("SELECT 1 FROM accounts WHERE user = ?", (user,))
            if cursor.fetchone() is None:
                response_payload = "error:norecipient"
            else:
                # Delete draft from sender
                cursor.execute("DELETE FROM drafts WHERE draft_id = ?", (draft_id,))

                # Add message to messages table
                # Note: `user` is the recipient
                # TODO: this exeuction part is not finishing
                cursor.execute("""
                    INSERT INTO messages (user, sender, msg, checked, inbox)
                    VALUES (?, ?, ?, ?, ?) RETURNING msg_id
                """, (user, sender, content, 0, 1))
                msgId = cursor.fetchone()
                response_payload = msgId[0]

                # We updated the user's database, now, can we immediately update inbox?
                # Check if recipient is logged in, and if so, send data
                cursor.execute("SELECT logged_in FROM accounts WHERE user = ?", (user,))
                logged_in = cursor.fetchone()
                
                if user in clients and logged_in:
                    recipient_response = f"{sender}:{content}:{msgId[0]}:{user}"
                    payload_bytes = recipient_response.encode("utf-8")
                    receive_message_type = 0x000D
                    header = struct.pack("!H I", receive_message_type, len(payload_bytes))
                    recipient_socket = clients[user]
                    recipient_socket.send(header + payload_bytes)  # Send the response to the client
                    logging.info("SERVER: message sent to user immediately!")
        
        elif message_type == 0x0006:  # Add Draft
            user, recipient, content, checked = payload.split(":")
            cursor.execute("INSERT INTO drafts (user, recipient, msg, checked) VALUES (?, ?, ?, ?) RETURNING draft_id", (user, recipient, content, checked))
            draft_id = cursor.fetchone()[0]
            response_payload = f"{draft_id}"
        
        elif message_type == 0x0007:  # Save Drafts
            user, drafts = payload.split(":", 1)
            # Edge case: when logging out, there are no drafts you made; just return ok
            if not drafts.strip():
                return "ok"
            drafts_dict = [dict(item.split('=') for item in entry.split(';')) for entry in drafts.split(',')]
            # Reset drafts
            cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
            # Add drafts to drafts table
            for draft in drafts_dict:
                recipient, msg = draft["recipient"], draft["msg"]
                cursor.execute("INSERT INTO drafts (user, recipient, msg, checked) VALUES (?, ?, ?, 0)", (user, recipient, msg))
            response_payload = "ok"
        
        elif message_type == 0x0008:  # Check Message
            user, msg_id = payload.split(":")
            cursor.execute("UPDATE messages SET checked = 1 WHERE user = ? AND msg_id = ?", (user, msg_id))
            response_payload = "ok"
        
        elif message_type == 0x0009:  # Download Message
            user, msg_id = payload.split(":")
            cursor.execute("UPDATE messages SET inbox = 0 WHERE user = ? AND msg_id = ?", (user, msg_id))
            response_payload = "ok"
        
        elif message_type == 0x000A:  # Delete Message
            user, msg_id = payload.split(":")
            cursor.execute("DELETE FROM messages WHERE AND msg_id = ?", (msg_id))
            response_payload = "ok"
        
        elif message_type == 0x000B:  # Delete Account
            user, pwd = payload.split(":")
            cursor.execute("SELECT uuid FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
            account = cursor.fetchone()
            if account is not None:
                cursor.execute("DELETE FROM messages WHERE user = ?", (user,))
                cursor.execute("DELETE FROM drafts WHERE user = ?", (user,))
                cursor.execute("DELETE FROM accounts WHERE user = ? AND pwd = ?", (user, pwd))
                response_payload = "ok"
            else:
                response_payload = "error:invalid"
        
        elif message_type == 0x000C:  # Logout
            user = payload
            cursor.execute("UPDATE accounts SET logged_in = 0 WHERE user = ?", (user,))
            response_payload = "ok"
            if user in clients:
                del clients[user]
        else:
            response_payload = "error:unknown"
        
        db.commit()
        if not connection:
            db.close()
        return response_payload
    except:
        return "error:unknown"


# ++++++++++ Main Functions: Handling Connections ++++++++++ #
def accept_wrapper(sock):
    """Accept connection from client."""
    conn, addr = sock.accept()
    logging.info(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    # clients[addr] = conn

def service_connection(key, mask):
    """Handle communication with client."""
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(config.BUF_SIZE)
        if recv_data:
            logging.info(f"Raw received data: {recv_data}")
            data.inb += recv_data
            
            while len(data.inb) >= 2:
                # Extract and unpack msg_type, payload_length
                msg_type = struct.unpack("!H", data.inb[:2])[0]         # Unsigned short (2 bytes)
                payload_length = struct.unpack("!I", data.inb[2:6])[0]  # Unsigned int (4 bytes)
                # Extract payload data
                payload_data = data.inb[6:6 + payload_length]
                message = payload_data.decode("utf-8")    
                # Remove processed data
                data.inb = data.inb[6 + payload_length:]                # 2 + 4 + payload_length
                logging.info(f"Processing message: {msg_type, message}")

                # Determine if login/create account request, and if so, store socket connection for this user
                if msg_type == 0x0001 or msg_type == 0x0003:
                    try:
                        user, _ = message.split(":", 1)
                        clients[user] = sock
                        logging.info(f"SERVER: {user} logged in and added to active clients.")
                    except ValueError:
                        logging.error("SERVER: Malformed login payload, expected 'user:pwd'")

                try:
                    response = process_request(msg_type, message)
                    response_bytes = response.encode("utf-8")
                    # submit bytes over the wire       
                    data.outb += response_bytes
                except Exception as e:
                    logging.error(f"Error processing message: {e}")
        else:
            logging.info(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            try:
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]  # Remove sent data from buffer
            except Exception as e:
                logging.error(f"Error sending response: {e}")


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