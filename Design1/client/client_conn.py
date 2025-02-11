# client_conn.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import errno
import os
import socket
import time
import uuid
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import logging
import threading
import select
import queue

listener_thread = None
listener_running = True
message_queue = queue.Queue()


# +++++++++++++++++++ Functions +++++++++++++++++++ #

def client_conn_create_account(user, pwd_hash):
    """ JSON: createAccount
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "createAccount": {
                "request": {
                    "action": "createAccount",
                    "data": {
                        "username": user,
                        "passwordHash": pwd_hash
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_create_account: response {response}")
    # See if successfully created account
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_create_account: JSONDecode {e}")
        return False
    
def client_conn_login(user, pwd_hash):
    """ JSON: login
    Return: [inboxCount, msgs, drafts] of user, else [] """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "login": {
                "request": {
                    "action": "login",
                    "data": {
                        "username": user,
                        "passwordHash": pwd_hash
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    # See if successfully logged in
    try:
        response_json = json.loads(response)
        if response_json.get("status") == "ok":
            inboxCount = response_json.get("data")["inboxCount"]
            old_msgs = response_json.get("data")["old_msgs"]
            inbox_msgs = response_json.get("data")["inbox_msgs"]
            drafts = response_json.get("data")["drafts"]
            return [inboxCount, old_msgs, inbox_msgs, drafts]
        return [0, [], [], []]
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_login: JSONDecode {e}")
        return [0, [], [], []]
    
def client_conn_get_pwd(user):
    """ JSON: listAccounts 
    Return: lists of account users, else []."""
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "getPwd": {
                "request": {
                    "action": "getPwd",
                    "data": {
                        "username": user
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response form server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    # Parse response from server
    try:
        response_json = json.loads(response)
        pwd_hash = response_json.get("data")
        if pwd_hash:
            return pwd_hash.get("passwordHash")
        else:
            return ""
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_get_pwd: JSONDecode {e}")
        return ""
    
def client_conn_list_accounts():
    """ JSON: listAccounts 
    Return: lists of account users, else []."""
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "listAccounts": {
                "request": {
                    "action": "listAccounts",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response form server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_list_accounts: response {response}")
    # Parse response from server
    try:
        response_json = json.loads(response)
        account_users = response_json.get("data")
        if not account_users:
            return []
        else:
            return account_users.get("accounts_users", [])
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_list_accounts: JSONDecode {e}")
        return []

def client_conn_send_message(draft_id, user, sender, content):
    """ JSON: sendMessage
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "sendMessage": {
                "request": {
                    "action": "sendMessage",
                    "data": {
                        "draft_id": draft_id,
                        "recipient": user,
                        "sender": sender,
                        "content": content
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    print(msg)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_send_message: response {response}")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return response_json["data"]["msgId"] if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_send_message: JSONDecode {e}")
        return False

def client_conn_add_draft(user, recipient, content, checked):
    """ JSON: addDraft
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "addDraft": {
                "request": {
                    "action": "addDraft",
                    "data": {
                        "user": user,
                        "recipient": recipient,
                        "content": content,
                        "checked": checked
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_add_draft: response {response}")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return response_json["data"]["draft_id"] if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_add_draft: JSONDecode {e}")
        return False

def client_conn_save_drafts(user, drafts):
    """ JSON: sendMessage
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "saveDrafts": {
                "request": {
                    "action": "saveDrafts",
                    "data": {
                        "user": user,
                        "drafts": drafts
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_save_drafts: response {response}")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_save_drafts: JSONDecode {e}")
        return False
    
def client_conn_check_message(user, msgId):
    """ JSON: checkMessage
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "checkMessage": {
                "request": {
                    "action": "checkMessage",
                    "data": {
                        "username": user,
                        "msgId": msgId
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_check_message: response {response}")
    # See if successfully checked message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_check_message: JSONDecode {e}")
        return False
    
def client_conn_download_message(user, msgId):
    """ JSON: downloadMessage
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "downloadMessage": {
                "request": {
                    "action": "downloadMessage",
                    "data": {
                        "username": user,
                        "msgId": msgId
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_download_message: response {response}")
    # See if successfully downloaded message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_download_message: JSONDecode {e}")
        return False

def client_conn_delete_message(user, msgId):
    """ JSON: checkMessage
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "deleteMessage": {
                "request": {
                    "action": "deleteMessage",
                    "data": {
                        "username": user,
                        "msgId": msgId
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_delete_message: response {response}")
    # See if successfully deleted message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_delete_message: JSONDecode {e}")
        return False
    
def client_conn_delete_account(user, pwd_hash):
    """ JSON: deleteAccount
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "deleteAccount": {
                "request": {
                    "action": "deleteAccount",
                    "data": {
                        "username": user,
                        "passwordHash": pwd_hash
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_delete_account: response {response}")
    # See if successfully deleted account
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_delete_account: JSONDecode {e}")
        return False
    
def client_conn_logout(user):
    """ JSON: logout
    Return: T for success, F for no success """
    # Set up request
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "logout": {
                "request": {
                    "action": "logout",
                    "data": {
                        "username": user,
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(f"CLIENT: client_conn_logout: response {response}")
    # See if successfully logged out
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError as e:
        logging.error(f"CLIENT: client_conn_logout: JSONDecode {e}")
        return False
    
def client_conn_receive_message(update_inbox_callback):
    """ Listens for new messages and updates the GUI via a callback function. """
    #s.setblocking(True)  # issue: when set to true, we have freezing, and when false, resource issues
    while listener_running:
        try:
            # Use select to check for socket readiness with a 2-second timeout
            ready, _, _ = select.select([s], [], [], 2)  # 2-second timeout
            if ready:
                try:
                    data = s.recv(config.BUF_SIZE)
                    if not data:  # If no data, the server closed the connection
                        logging.info("CLIENT: client_conn_receive_message: no data, connection closed by server.")
                        break
                    data = data.decode("utf-8")
                    logging.info(f"CLIENT: client_conn_receive_message: data {data}")

                    # Process the message if it's in the expected format
                    try:
                        server_msg = json.loads(data)

                        if "action" in server_msg and server_msg.get("action") == "receiveMessage":
                            msgId = server_msg["msgId"]
                            user = server_msg["user"]
                            sender = server_msg["sender"]
                            msg = server_msg["msg"]

                            incoming_msg = {
                                "msg_id": msgId,
                                "user": user,
                                "sender": sender,
                                "msg": msg,
                                "checked": 0,
                                "inbox": True
                            }

                            # update the GUI
                            update_inbox_callback(incoming_msg)

                    except json.JSONDecodeError as e:
                        logging.error(f"CLIENT: client_conn_receive_message: JSONDecodeError {e}")
                except socket.error as e:
                    # Handle non-blocking socket error, this error is expected when no data is available
                    if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        time.sleep(0.1)  # Sleep briefly before trying again (avoid busy loop)
                    else:
                        logging.error(f"CLIENT: client_conn_receive_message: socket error {e}")
        except socket.timeout:
            # Handle socket timeout if necessary, otherwise just pass
            pass
        except Exception as e:
            logging.error(f"CLIENT: client_conn_receive_message: Unexpected Exception {e}")
            break  # Exit the loop in case of an unexpected error



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