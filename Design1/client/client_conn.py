# client_conn.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import socket
import uuid
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import logging
import threading
import select
#import gui


# +++++++++++++++++++ Functions +++++++++++++++++++ #

def client_conn_create_account(user, pwd):
    """ JSON: createAccount
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "createAccount": {
                "request": {
                    "requestId": request_id,
                    "action": "createAccount",
                    "data": {
                        "username": user,
                        "passwordHash": pwd
                    }
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    logging.info(msg)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    logging.info(response)
    # See if successfully created account
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_login(user, pwd):
    """ JSON: login
    Return: [inboxCount, msgs, drafts] of user, else [] """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "login": {
                "request": {
                    "requestId": request_id,
                    "action": "login",
                    "data": {
                        "username": user,
                        "passwordHash": pwd
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
    print(response)
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
    except json.JSONDecodeError:
        return [0, [], [], []]
    
def client_conn_get_pwd(user):
    """ JSON: listAccounts 
    Return: lists of account users, else []."""
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "getPwd": {
                "request": {
                    "requestId": request_id,
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
    except json.JSONDecodeError:
        return ""
    
def client_conn_list_accounts():
    """ JSON: listAccounts 
    Return: lists of account users, else []."""
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "listAccounts": {
                "request": {
                    "requestId": request_id,
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
    print(response)
    # Parse response from server
    try:
        response_json = json.loads(response)
        account_users = response_json.get("data")
        if not account_users:
            return []
        else:
            return account_users.get("accounts_users", [])
    except json.JSONDecodeError:
        return []

def client_conn_send_message(draft_id, user, sender, content):
    """ JSON: sendMessage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "sendMessage": {
                "request": {
                    "requestId": request_id,
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
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.BUF_SIZE)
    response = data.decode("utf-8")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False

def client_conn_add_draft(user, recipient, content, checked):
    """ JSON: addDraft
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "addDraft": {
                "request": {
                    "requestId": request_id,
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
    logging.info(f"ADDED DRAFT ID RESPONSE: {response}")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False

def client_conn_save_drafts(user, drafts):
    """ JSON: sendMessage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "saveDrafts": {
                "request": {
                    "requestId": request_id,
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
    logging.info(f"SAVE DRAFTs RESPONSE: {response}")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_check_message(user, msgId):
    """ JSON: checkMessage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "checkMessage": {
                "request": {
                    "requestId": request_id,
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
    # See if successfully checked message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_download_message(user, msgId):
    """ JSON: downloadMessage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "downloadMessage": {
                "request": {
                    "requestId": request_id,
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
    # See if successfully downloaded message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False

def client_conn_delete_message(user, msgId):
    """ JSON: checkMessage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "deleteMessage": {
                "request": {
                    "requestId": request_id,
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
    # See if successfully deleted message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_delete_account(user, pwd):
    """ JSON: deleteAccount
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "deleteAccount": {
                "request": {
                    "requestId": request_id,
                    "action": "deleteAccount",
                    "data": {
                        "username": user,
                        "passwordHash": pwd
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
    # See if successfully deleted account
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_logout(user):
    """ JSON: logout
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "logout": {
                "request": {
                    "requestId": request_id,
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
    print(response)
    # See if successfully logged out
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_receive_message(s):
    while True:
        try:
            ready, _, _ = select.select([s], [], [], 2)  # 2-second timeout
            if ready:
                data = s.recv(config.BUF_SIZE)
                if not data:
                    logging.warning("SERVER: Connection closed by server.")
                    break  # Exit the loop if no data received, indicating server disconnected
                data = data.decode("utf-8")
                logging.info(f"CLIENT: Received message: {data}")
                # Here we assume the message is JSON formatted
                try:
                    server_msg = json.loads(data)
                    # Handle the action from the server
                    if server_msg.get("action") == "receiveMessage":
                        msgId = server_msg.get("msgId")
                        user = server_msg.get("user")
                        sender = server_msg.get("sender")
                        msg = server_msg.get("msg")
                        incoming_msg = {"msg_id":msgId, "user":user, "sender":sender, "content":msg, "checkbox":0, "inbox":True}
                        #gui.db_user_data[1].append(incoming_msg)
                        #gui.create_new_unread_msg(incoming_msg)

                        logging.info(f"CLIENT: Received message from {sender}: {msg}")
                        print(f"Received message from {sender}: {msg}")
                    else:
                        logging.warning("CLIENT: Unknown action received.")
                except json.JSONDecodeError:
                    logging.error("CLIENT: Failed to decode the JSON message.")
        except socket.timeout:
            pass
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
