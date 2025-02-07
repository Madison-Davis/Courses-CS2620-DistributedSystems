# client_conn.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import socket
import uuid
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config



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
    s.sendall(msg.encode("utf-8"))
    # Receive response form server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
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
    # Receive response form server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully created account
    try:
        response_json = json.loads(response)
        if response_json.get("status") == "ok":
            inboxCount = response_json.get("inboxCount")
            msgs = response_json.get("msgs")
            drafts = response_json.get("drafts")
            return [inboxCount, msgs, drafts]
        return []
    except json.JSONDecodeError:
        return []
    
def client_conn_list_accounts():
    """ JSON: listAccounts 
    Return: lists of account users and passwords, else [], []."""
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
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # Parse response from server
    try:
        response_json = json.loads(response)
        account_users = response_json.get("data").get("accounts_users", [])
        account_pwds = response_json.get("data").get("accounts_pwds", [])
        return account_users, account_pwds
    except json.JSONDecodeError:
        return [], []

def client_conn_send_message(user, draftId):
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
                    "content": draftId
                    }
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
    # See if successfully created account
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
                     "msgIds": msgId
                    }
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
    # See if successfully created account
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
                     "msgIds": msgId
                    }
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
    # See if successfully created account
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
    # Receive response form server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully created account
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
    # Receive response form server
    data = s.recv(config.PORT)
    response = data.decode("utf-8")
    # See if successfully created account
    try:
        response_json = json.loads(response)
        return True if response_json.get("status") == "ok" else False
    except json.JSONDecodeError:
        return False
    
if __name__ == "main":
    # this will request to the server to accept the connection for future data I/O
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((config.HOST, config.PORT))