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
def client_conn_list_accounts():
    """ Create a request ID, a request JSON """
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
    message = json.dumps(request)
    s.sendall(message.encode("utf-8"))
    # Receive response form server
    data = s.recv(1024)
    response = data.decode("utf-8")
    # Parse response from server
    try:
        response_json = json.loads(response)
        accounts = response_json.get("data", {})
        return accounts
    except json.JSONDecodeError:
        return []


if __name__ == "main":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((config.HOST, config.PORT))