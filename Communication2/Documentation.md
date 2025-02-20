# CS 2620 Communication 2: gRPC

-------------------------------------------
## Design Requirements

This project requires the construction of a simple client-server chat application utilizing gRPC.  GUI is required and connection information is stored as a config.  The following requirements were carried over from the previous iteration of this project: https://github.com/Madison-Davis/Courses-CS2620-DistributedSystems/blob/main/Design1/Documentation.md

1. Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.
2. Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.
3. List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.
4. Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.
5. Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.
6. Delete a message or set of messages. Once deleted messages are gone.
7. Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.



-------------------------------------------
## Setup

Clone the repository.
Generate Python gRPC files: Navigate to comm/ and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto`
Replace `import chat_pb2 as chat__pb2` with `from comm import chat_pb2 as chat__pb2` in `chat_pb2_grpc.py`

Run server:
`py -m server.server`

Run client GUI:
`py -m client.gui`

Run unit tests:
`py -m unittest tests.tests_rpc`


-------------------------------------------
## Code Structure

```
├── client
│   ├── chat_client.py       → ChatClient class, functions to request/receive from server
│   ├── gui.py               → creates GUI for client
├── comm
│   ├── chat.proto           → defines gRPC services and messages for requests/responses
│   ├── chat_pb2.py          → generated code from compiler: for all .proto service/rpc defs
│   ├── chat_pb2_grpc.py     → generated code from compiler: for all .proto message defs
├── config
│   ├── config.py            → defines HOST/PORT and other parameters
├── server
│   ├── server.py            → ChatService class, functions to use SQL and return results
│   ├── server_security.py   → for password hashing
└── Documentation.md
```

The user interface is run on `gui.py`, which instantiates a `ChatClient` and makes function calls to it. In `chat_client.py`, the `ChatClient` makes calls to a Chat Service Stub, which has its request and response types outlined in `chat.proto`. A `ChatService` is instantiated with the setup tasks of database initialization. When the `ChatService` receives an action request, it implements the appropriate SQL calls in `server.py`. 


-------------------------------------------
## Assumptions

We assume no requirements for persistent storage, that is, if the server shuts down and reboots, it does not need to keep the information it had prior to the shutdown.
We assume no grouping of messages. In other words, messages are stand-alone with no history-attached, similar to a Gmail-styled application.
We assume “undelivered messages” refers to messages that have yet to be delivered by a sender. We will often refer to these as “drafts” which are displayed on the sender’s side.
We assume the recipient of messages is the one who can specify the number of messages they want delivered. We refer to undelivered messages as “inbox messages” and delivered messages as “downloaded messages.”
