# CS 2620 Design Exercise 3: Replication

-------------------------------------------
## Design Requirements

This design exercise requires us to take our previous chat application implementation and re-design and re-implement it so that the system is both persistent (it can be stopped and re-started without losing messages that were sent during the time it was running) and 2-fault tolerant in the face of crash/failstop failures. In other words, replicate the back end of the implementation, and make the message store persistent.

The replication can be done in multiple processes on the same machine, but the replication should also work over multiple machines (at least two). Do not share a persistent store; this would introduce a single point of failure.

Extra Credit: Build your system so that it can add a new server into its set of replicas.

-------------------------------------------
## Setup

Clone the repository.
Generate Python gRPC files: Navigate to comm/ and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto`
Replace `import chat_pb2 as chat__pb2` with `from comm import chat_pb2 as chat__pb2` in `chat_pb2_grpc.py`

Set `PID = 0` in `config/config.py`.

Run server (3 separate instances):
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

1. We assume that each server must keep track of their own copy of active replicas, who the leader currently is, and their own copy of the chat database. However, we assume that all servers upon startup know that the possible replicas are with PIDs 0, 1, and 2, hence the global dictionary of replica IDs and addresses in `config.py`. This part of the file is unchanged, so we are not sharing global information about which replicas are active and which are killed.
2. We use the leader election mechanism that designates the active replica with the lowest PID as the new leader.
3. The leader only sends replication instruction to the replicas if they receive a write operation (CreateAccount, Login, SendMessage, AddDraft, SaveDrafts, CheckMessage, DownloadMessage, DeleteMessage, DeleteAccount, Logout, ReceiveMessageStream)
4. The heartbeat mechanism is assumed to have all replicas communicate with every other replica, including the leader.


-------------------------------------------
## Demo Plan

1. Persistent storage: We will show that old messages from previous server startup are still there after you shut down the server and restart it.
2. 2-fault tolerance: We will show that chat application can still function after all possible orders of failure.
- Replica 2 ⇒ Replica 3
- Replica 3 ⇒ Replica 2
- Leader ⇒ Replica 2
- Replica 2 ⇒ Leader
- Leader ⇒ Replica 3
- Replica 3 ⇒ Leader


-------------------------------------------
## GUI Design

Login Frame: provides entries for username input and password input, as well as a button to submit the information. Initially, only the username entry is displayed. Upon entering a name, the client makes a request to the server to determine if they are a new user or not. This then displays the password input along with a textual message specific to whether the user is new (“Welcome, new user!”) or not (“Welcome back!”). Upon entering the password and clicking enter, the user is brought to the main frame. If the user is returning, additional data about past drafts or messages are displayed.

Main Frame: The top area is reserved for a logout button, delete account button, and greeting message specifying the current username. The rest of the area is split into two main sections: received messages and drafts.
1. Inbox: a title that states “inbox” with the number of emails currently in the inbox, and an “open inbox” button with a specification for the number of emails desired to be opened (this number can be edited by the user via a dropdown menu). Upon clicking the button, new messages pop up at the top of the “messages” area. Messages are sent to the inbox whenever a user receives a message.
2. Messages: rows of messages, where each message has a delete button, an unchecked mark/unread, and the message displayed as [Sender: Message]. Messages are sent here if they have already been opened but not deleted before logging out, or if the user is logged in and receives a new message. Messages can also be checked as read, which persist even if the user logs out and logs back in.
3. Drafts: A list of drafts yet to be sent, along with a “Send” button and “Select All” button. Each draft contains a select button, an entry field to type in the message, edit button, save button, and a dropdown list for accounts.



-------------------------------------------
## Protocol Design

We utilized gRPC to design how messages were to be sent to/from the client/server.  We encourage you to look into the `chat.proto` file for the complete list of all of our services and messages.  We will highlight the main ones here.

All of our services to adhere to the design requirements are shown here.  Most are unary responses with the exception of receive message.  Because the client will not know when they are receiving a message, we instantiate a thread to request to receive and then constantly listen for any stream of information coming back from the server.  The client, upon receiving a message, will then act accordingly.  The server keeps a list of all logged-in users to know whether to send a message immediately or store in that user's inbox for the time being.
```
service ChatService {
    rpc CreateAccount(CreateAccountRequest) returns (GenericResponse);                          → create account
    rpc Login(LoginRequest) returns (LoginResponse);                                            → login 
    rpc GetPassword(GetPasswordRequest) returns (GetPasswordResponse);                          → get password
    rpc ListAccounts(ListAccountsRequest) returns (ListAccountsResponse);                       → list accounts
    rpc SendMessage(SendMessageRequest) returns (SendMessageResponse);                          → send message
    rpc AddDraft(AddDraftRequest) returns (AddDraftResponse);                                   → add draft
    rpc SaveDrafts(SaveDraftsRequest) returns (GenericResponse);                                → save drafts
    rpc CheckMessage(CheckMessageRequest) returns (GenericResponse);                            → check message
    rpc DownloadMessage(DownloadMessageRequest) returns (GenericResponse);                      → download message
    rpc DeleteMessage(DeleteMessageRequest) returns (GenericResponse);                          → delete message
    rpc DeleteAccount(DeleteAccountRequest) returns (GenericResponse);                          → delete account
    rpc Logout(LogoutRequest) returns (GenericResponse);                                        → logout
    rpc ReceiveMessageStream(ReceiveMessageRequest) returns (stream ReceiveMessageResponse);    → receive message (instant/logged in)
    rpc Replicate(ReplicationRequest) returns (GenericResponse);                                → tell replica to replicate
    rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);                                → send heartbeat ping
    rpc GetLeader(GetLeaderRequest) returns (GetLeaderResponse);                                → get current leader
}
```

Our main message types:
```
message Message {
    int32 msg_id = 1;
    string username = 2;
    string sender = 3;
    string msg = 4;
    bool checked = 5;
    bool inbox = 6;
}

message Draft {
    int32 draft_id = 1;
    string username = 2;
    string recipient = 3;
    string msg = 4;
    bool checked = 5;
}
```


-------------------------------------------
## Server Data: SQL

Format: [COLUMN]: [TYPE], [DEFAULT]

Accounts Database
1. uuid: int, N/A (no default; should not be in DB)
2. username: str, N/A (no default; should not be in DB)
3. pwd: str, N/A (no default; should not be in DB)
4. logged_in: bool, 0
   
Messages Database
1. msg_id: int, N/A (no default; should not be in DB)
2. username: str, N/A (no default; should not be in DB)
3. sender: str, N/A (no default; should not be in DB)
4. msg: str, N/A (no default; should not be in DB)
5. checked: bool, 0
6. inbox: bool, 1

Drafts Database
1. draft_id: int, N/A (no default; should not be in DB)
2. username: str, N/A (no default; should not be in DB)
3. recipient: str, ""
4. msg: str, ""
5. checked: bool, 0


-------------------------------------------
## Servers: Replication

- How do servers keep track of other replicas?
    - Global known information about all possible replicas and their addresses are contained in `REPLICA_ADDRESSES`, a dictionary with PID as the key and address as the value.
    - Each server contains a local copy of `self.active_servers`, which is a dictionary storing all active servers. The key is PID and the value is the most recent heartbeat timestamp.
- How does the heartbeat mechanism work?
    - In `config.py`, `HEARTBEAT_INTERVAL` denotes the amount of seconds that pass between every heartbeat ping, and `HEARTBEAT_TIMEOUT` denotes the amount of seconds that pass without a response from a replica until we assume it is dead.
    - In `server.py`, we run a `heartbeat_loop()` that sends a `HeartbeatRequest` to every active server (including the leader), updates the most recent timestamp for active servers, removes servers that either do not respond to the hartbeat ping or haven't responded in a while, and call `trigger_leader_election()` to elect a new leader in the case that the existing leader has died.
- How do replicas replicate leader behavior?
    - In `server.py`, the leader can call `Replicate()` to tell a specific replica to replicate a write operation. The replica parses and deserializes the payload and calls the appropriate local method request, returning True if the replication was successful. 
    - Note that `replicate_to_replicas()` is a helper function that the leader uses to check which replicas are still alive and call `Replicate()` for each active server.
- How will the client know to reconnect to the new leader in case the old leader dies?
    - Every existing client function is now wrapped in a try except block to call `reconnect()` upon catching a gRPC error, which indicates that the existing leader is no longer active.
    - In `reconnect()`, the client will call `get_leader()` to find the new leader PID and connect to the new leader's address.

-------------------------------------------
## Client Data: Datastructures

The server works with a SQL database, but the client also deals with local data. The client deals with (1) caching the results of the SQL database as well as (2) keeping tabs on information that will eventually be sent back to the database to update, insert, or delete items in the database. Specifically, for each client, the following data structures are used:

1. db_user_data: used to hold information from the SQL database.
    1. inboxCount: the number of items in the inbox
    2. old_msgs: all database entries of messages that have been downloaded and are shown visibly in the “Messages” section of the GUI.
    3. inbox_msgs: all database entries of messages that have not been downloaded and are hidden in the “Inbox” section of the GUI.
    4. drafts: all database entries of drafts that are shown visibly in the “Drafts” section of the GUI.
2. db_accounts: used to hold account usernames from the SQL database.
3. drafts_XXX: used for drafts. Drafts are saved to the SQL database upon creation and can be edited when the user explicitly pushes “Save”. We would like a complete list of all the drafts and their information at any given time, even if some are not meant to be sent to the server quite yet. These data structures accomplish this function of holding this information. Values are strings separated by commas, where their index represents the row they show up in in the GUI.
    1. drafts_msgs: stores draft message content
    2. drafts_recipients: stores draft message recipients
    3. drafts_checkmarks: stores all draft messages that are checked to be sent



-------------------------------------------
## Robustness: Password Security

To ensure password security, we store all password information as hashed passwords. We use a randomly generated salt using SHA-256 via hashlib to generate hashed passwords and verify hashes against user-inputted passwords.



-------------------------------------------
## Robustness: Testing



-------------------------------------------
## Code Cleanliness

To ensure code cleanliness, we adhered to the code structure as articulated in an earlier section.  We also did the following:
1. For tests_rpc.py, server.py, and chat_client.py, we instantiated them as classes.
2. For all functions in tests_rpc.py, server.py, chat_client.py, and gui.py, we put comments under each function header to help readers understand its implementation.
3. For gui.py, because we did not use a class but rather a set of functions, we made comments more robust beyond just header functions by utilizing sectioning-comments to "divide and sort" the functions based on usage.  For example, we have sections for logging in, logging out or deleting accounts, receiving messages in real time ("event listeners"), GUI loading frames, GUI loading features on existing frames, and GUI frame button-handling (if a button is clicked, for example).
4. For gui.py, we did the same "divide and sort" sectioning for variables.  We have sections for GUI variables and client data variables.






