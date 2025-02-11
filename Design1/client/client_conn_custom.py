# client_conn_custom.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import socket
import uuid
import struct
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import logging
import threading
import time
import errno
import re
import ast
import select

# 0x0001: Login
# 0x0002: Send Message
# 0x0003: Create Account
# 0x0004: List Accounts
# 0x0005: Get Password
# 0x0006: Add Draft
# 0x0007: Save Drafts
# 0x0008: Check Message
# 0x0009: Download Message
# 0x000A: Delete Message
# 0x000B: Delete Account
# 0x000C: Logout
# 0x000D: Receive Message

# +++++++++++++++++++ Functions +++++++++++++++++++ #

def send_request(message_type, payload):
    """Sends a request using the custom wire protocol."""
    payload_bytes = payload.encode("utf-8")
    header = struct.pack("!H I", message_type, len(payload_bytes))
    s.sendall(header + payload_bytes)

def receive_response():
    """Receives a response from the server using the custom wire protocol."""
    response_bytes = s.recv(config.BUF_SIZE)  # Read raw bytes from the socket
    response = response_bytes.decode("utf-8")  # Decode bytes to string
    return response

def client_conn_create_account(user, pwd):
    payload = f"{user}:{pwd}"
    send_request(0x0003, payload)
    response = receive_response()
    print("client_conn_create_account", response)
    return True if response == "ok" else False

def client_conn_login(user, pwd):
    """Returns inboxCount, old_msgs, inbox_msgs, drafts"""
    payload = f"{user}:{pwd}"
    send_request(0x0001, payload)
    response = receive_response()
    print("client_conn_login", response)
    if response == "error:invalid":
        return [0, [], [], []]
    else:
        # Use regular expresisons to find and match groups
        pattern = r"\[(\d+),\s*(\[.*\])\,\s*(\[.*\])\,\s*(\[.*\])\]"
        # - \[(\d+) -> Captures the inbox count (0)
        # - (\[.*\]) -> Captures the 1st list
        # - (\[.*\]) -> Captures the 2nd list
        # - (\[.*\]) -> Captures the 3rd list
        match = re.match(pattern, response)
        inbox_count = int(match.group(1))
        old_msgs_str = match.group(2)
        inbox_msgs_str = match.group(3)
        drafts_str = match.group(4)
        # Evaluate strings into lists/dictionaries
        try:
            old_msgs_list = ast.literal_eval(old_msgs_str.replace("'", '"'))
            inbox_msgs_list = ast.literal_eval(inbox_msgs_str.replace("'", '"'))
            drafts_list = ast.literal_eval(drafts_str.replace("'", '"'))
        except Exception as e:
            print(f"ERROR: client_conn_login: {e}")
            return [0, [], [], []]
        return [inbox_count, old_msgs_list, inbox_msgs_list, drafts_list]

def client_conn_list_accounts():
    """Returns list of all existing account usernames."""
    send_request(0x0004, "")
    response = receive_response()
    print("client_conn_list_accounts:", response.split(":", 1)[1])
    if response: # turn "num_users:user1,user2,user3" into ["user1", "user2", "user3"]
        split_response = response.split(":", 1)
        if len(split_response) > 1: # edge case: if there are no users
            return split_response[1].split(",") if split_response[1] else []
    return []

def client_conn_get_pwd(user):
    """Returns password hash of requested username."""
    send_request(0x0005, user)
    response = receive_response()
    print("client_conn_get_pwd:", response)
    return "" if response == "error:exist" else response

def client_conn_send_message(draft_id, user, sender, content):
    payload = f"{draft_id}:{user}:{sender}:{content}"
    print(payload)
    send_request(0x0002, payload)
    response = receive_response()
    print("client_conn_send_message:", response)
    return response

def client_conn_add_draft(user, recipient, content, checked):
    """Returns newly assigned draft ID of draft."""
    payload = f"{user}:{recipient}:{content}:{checked}"
    send_request(0x0006, payload)
    response = receive_response()
    print("client_conn_add_draft:", response)
    return response

def client_conn_save_drafts(user, drafts):
    # user      = "asd"
    # drafts    = [{'draft_id': 2, 'user': 'asd', 'recipient': '', 'msg': 'hello!', 'checked': 0},
    #               {'draft_id': 3, 'user': 'asd', 'recipient': '', 'msg': 'hi!', 'checked': 0}]
    # asd:draft_id=2;user=asd;recipient=;msg=hello!;checked=0,draft_id=3;user=asd;recipient=;msg=hi!;checked=0
    payload = f"{user}:{','.join([';'.join([f'{k}={v}' for k, v in draft.items()]) for draft in drafts])}"
    send_request(0x0007, payload)
    response = receive_response()
    print("client_conn_save_drafts:", response)
    return True if response == "ok" else False

def client_conn_check_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x0008, payload)
    response = receive_response()
    print("client_conn_check_message:", response)
    return True if response == "ok" else False

def client_conn_download_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x0009, payload)
    response = receive_response()
    print("client_conn_download_message:", response)
    return True if response == "ok" else False

def client_conn_delete_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x000A, payload)
    response = receive_response()
    print("client_conn_delete_message:", response)
    return True if response == "ok" else False

def client_conn_delete_account(user, pwd):
    payload = f"{user}:{pwd}"
    send_request(0x000B, payload)
    response = receive_response()
    print("client_conn_delete_account:", response)
    return True if response == "ok" else False

def client_conn_logout(user):
    send_request(0x000C, user)
    response = receive_response()
    print("client_conn_logout:", response)
    return True if response == "ok" else False

import struct

def client_conn_receive_message(update_inbox_callback):
    """ Listens for new messages and updates the GUI via a callback function. """
    while True:
        try:
            # Use select to check for socket readiness with a 2-second timeout
            ready, _, _ = select.select([s], [], [], 2)  # 2-second timeout
            if ready:
                try:
                    # Grab header (6 bytes: 2 for type, 4 for length)
                    # TODO: change this?
                    header = s.recv(6)
                    if not header:
                        logging.info("CLIENT: Connection closed by server.")
                        break
                    receive_message_type, payload_length = struct.unpack("!H I", header)
                    if receive_message_type != 0x000D:
                        logging.warning(f"CLIENT: client_conn_receive_message: unexpected message type {receive_message_type}")
                        continue  # Ignore unexpected message types

                    # Grab payload based on length
                    payload_bytes = s.recv(payload_length)
                    if not payload_bytes:
                        logging.warning("CLIENT: client_conn_receive_message: empty payload received.")
                        continue
                    data = payload_bytes.decode("utf-8")
                    logging.info(f"CLIENT: client_conn_receive_message: received message data: {data}")

                    # Extract message details from payload (format: "sender:msg:draft_id:user")
                    if ":" in data:
                        sender, msg, msg_id, user = data.split(":", 3) # grabs 4 parts
                    else:
                        logging.warning("CLIENT: client_conn_receive_message: malformed message received.")
                        continue
                    
                    # Construct argument for update_inbox_callback and call function
                    incoming_msg = {
                        "msg_id": msg_id.strip(), 
                        "user": user.strip(), 
                        "sender": sender.strip(),
                        "msg": msg.strip(),
                        "checked": 0,
                        "inbox": True
                    }
                    update_inbox_callback(incoming_msg)

                except socket.error as e:
                    # Handle non-blocking socket error
                    if e.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
                        time.sleep(0.1)  # Sleep briefly before retrying
                    else:
                        logging.error(f"CLIENT: Socket error {e}")
        except socket.timeout:
            pass  # Handle timeout if necessary
        except Exception as e:
            logging.error(f"CLIENT: Unexpected Exception {e}")
            break  # Exit on unexpected errors


# +++++++++++++++++++ Logging +++++++++++++++++++ #
logging.basicConfig(
    level=logging.DEBUG,  # Change to logging.INFO to reduce verbosity
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),  # Save logs to a file
        logging.StreamHandler()  # Show logs in the console
    ]
)


# +++++++++++++++++++ Server +++++++++++++++++++ #
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((config.HOST, config.PORT))