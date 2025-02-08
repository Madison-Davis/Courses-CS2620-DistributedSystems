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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Account created successfully.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "An account with that username already exists.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    logging.info(msg)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Login successful.",
                    "data": {
                    "inboxCount": 0,
                    "old_msgs": [],
                    "inbox_msgs": [],
                    "drafts": []
                    }
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Invalid credentials.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully logged in
    try:
        response_json = json.loads(response)
        if response_json.get("status") == "ok":
            inboxCount = response_json.get("inboxCount")
            old_msgs = response_json.get("old_msgs")
            inbox_msgs = response_json.get("inbox_msgs")
            drafts = response_json.get("drafts")
            return [inboxCount, old_msgs, inbox_msgs, drafts]
        return []
    except json.JSONDecodeError:
        return []
    
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "",
                    "data": {
                    "passwordHash": ""
                    }
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "User does not exist or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response form server
    data = s.recv(config.PORT)
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
        return []
    
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "",
                    "data": {
                        "accounts_users": [],
                        "totalCount": 0
                    }
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Not authenticated or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response form server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
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

def client_conn_send_message(user, sender, content):
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
                        "recipient": user,
                        "sender": sender,
                        "content": content
                    }
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Message sent (and delivered/stored).",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Recipient does not exist or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Draft saved.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Cannot save draft or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully sent message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_check_message(user, msgId):
    """ JSON: checkMesssage
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Message checked as read.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Message unable to read or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully checked message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
def client_conn_download_message(user, msgId):
    """ JSON: downloadMesssage
    Return: T for success, F for no success """
    # Set up request
    request_id = str(uuid.uuid4())
    request = {
        "protocolVersion": 1,
        "description": "Simple client-server chat application JSON wire protocol",
        "actions": {
            "downloadMesssage": {
                "request": {
                    "requestId": request_id,
                    "action": "downloadMesssage",
                    "data": {
                        "username": user,
                        "msgId": msgId
                    }
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Message downloaded from inbox.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Message unable to download or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully downloaded message
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False

def client_conn_delete_message(user, msgId):
    """ JSON: checkMesssage
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Message deleted.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Not authorized to delete or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Account and all messages have been deleted.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Invalid credentials or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
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
                },
                "successResponse": {
                    "requestId": request_id,
                    "status": "ok",
                    "msg": "Logged out successfully.",
                    "data": {}
                },
                "errorResponse": {
                    "requestId": request_id,
                    "status": "error",
                    "msg": "Not logged in or other error.",
                    "data": {}
                }
            }
        }
    }
    # Send request
    msg = json.dumps(request)
    s.sendall(msg.encode("utf-8"))
    # Receive response from server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully logged out
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
if __name__ == "main":
    # this will request to the server to accept the connection for future data I/O
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((config.HOST, config.PORT))