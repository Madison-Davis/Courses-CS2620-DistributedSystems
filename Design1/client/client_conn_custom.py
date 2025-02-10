import sys
import os
import socket
import uuid
import struct
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import logging
import threading

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


def send_request(message_type, payload):
    """Sends a request using the custom wire protocol."""
    payload_bytes = payload.encode("utf-8")
    header = struct.pack("!H I", message_type, len(payload_bytes))
    s.sendall(header + payload_bytes)

def receive_response():
    """Receives a response from the server using the custom wire protocol."""
    header = s.recv(6)
    if len(header) < 6:
        return None
    message_type, payload_length = struct.unpack("!H I", header)
    payload = s.recv(payload_length).decode("utf-8")
    return payload

def client_conn_create_account(user, pwd):
    payload = f"{user}:{pwd}"
    send_request(0x0003, payload)
    response = receive_response()
    return response == "ok"

def client_conn_login(user, pwd):
    """Returns inboxCount, old_msgs, inbox_msgs, drafts"""
    payload = f"{user}:{pwd}"
    send_request(0x0001, payload)
    response = receive_response()
    return response.split(":") if response else [0, [], [], []]

def client_conn_list_accounts():
    """Returns list of all existing account usernames."""
    send_request(0x0004, "")
    response = receive_response()
    return response.split(":") if response else []

def client_conn_get_pwd(user):
    """Returns password hash of requested username."""
    send_request(0x0005, user)
    return receive_response()

def client_conn_send_message(draft_id, user, sender, content):
    payload = f"{draft_id}:{user}:{sender}:{content}"
    send_request(0x0002, payload)
    response = receive_response()
    return response == "ok"

def client_conn_add_draft(user, recipient, content, checked):
    """Returns newly assigned draft ID of draft."""
    payload = f"{user}:{recipient}:{content}:{checked}"
    send_request(0x0006, payload)
    return receive_response()

def client_conn_save_drafts(user, drafts):
    payload = f"{user}:{','.join(';'.join(f"{k}={v}" for k, v in drafts.items()))}"
    send_request(0x0007, payload)
    response = receive_response()
    return response == "ok"

def client_conn_check_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x0008, payload)
    response = receive_response()
    return response == "ok"

def client_conn_download_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x0009, payload)
    response = receive_response()
    return response == "ok"

def client_conn_delete_message(user, msgId):
    payload = f"{user}:{msgId}"
    send_request(0x000A, payload)
    response = receive_response()
    return response == "ok"

def client_conn_delete_account(user, pwd):
    payload = f"{user}:{pwd}"
    send_request(0x000B, payload)
    response = receive_response()
    return response == "ok"

def client_conn_logout(user):
    send_request(0x000C, user)
    response = receive_response()
    return response == "ok"

def client_conn_receive_message(s):
    while True:
        try:
            header = s.recv(6)
            if len(header) < 6:
                logging.warning("SERVER: Connection closed by server.")
                break
            message_type, payload_length = struct.unpack("!H I", header)
            payload = s.recv(payload_length).decode("utf-8")
            logging.info(f"CLIENT: Received message: {payload}")
            print(f"Received: {payload}")
        except Exception as e:
            logging.error(f"CLIENT: Error receiving message: {e}")

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
threading.Thread(target=client_conn_receive_message, args=(s,), daemon=True).start()