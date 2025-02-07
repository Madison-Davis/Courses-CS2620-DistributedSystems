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



# +++++++++++++++++++  Variables  +++++++++++++++++++ #
sel = selectors.BaseSelector



# ++++++++++++ Functions: Processing Requests ++++++++++++ #
def process_request(request):
    """Process JSON request from client and return response."""
    try:
        request_json = json.loads(request)
        action = request_json.get("actions", {})

        if "createAccount" in action:
            # TODO: SQL
            response = {}
        elif "login" in action:
            # TODO: SQL
            response = {}
        elif "listAccounts" in action:
            # TODO: SQL
            response = {}
        elif "sendMessage" in action:
            # TODO: SQL, Client Outbound Connection
            response = {}
        elif "checkMessage" in action:
            # TODO: SQL
            response = {}
        elif "deleteMessage" in action:
            # TODO: SQL
            response = {}
        elif "deleteAccount" in action:
            # TODO: SQL
            response = {}
        elif "logout" in action:
            # TODO: SQL
            response = {}
        else:
            # TODO: Error
            repsonse = {}
        return json.dumps(response).encode("utf-8")
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON"}).encode("utf-8")





# ++++++++++ Main Functions: Handling Connections ++++++++++ #
def accept_wrapper(sock):
    """Accept connection from client."""
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
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
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    # If client requests for us to do a task:
        # decode task
        # process task
        # format response into JSON
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            return_data = process_request(data.inb.decode("utf-8"))
            return_data = return_data.encode("utf-8")
            sent = sock.send(return_data)
            data.outb = data.outb[sent:]

def start_server():
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((config.HOST, config.PORT))
    lsock.listen()
    print("Listening on", (config.HOST, config.PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

if __name__ == "__main__":
    start_server()
