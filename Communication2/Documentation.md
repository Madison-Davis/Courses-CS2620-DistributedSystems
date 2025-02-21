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

1. We utilize persistent storage, but assume this is not required.  Persistent storage means that if the server shuts down and reboots, it does not need to keep the information it had prior to the shutdown.
2. We assume no grouping of messages. In other words, messages are stand-alone with no history-attached, similar to a Gmail-styled application.
3. We assume “undelivered messages” refers to messages that have yet to be delivered by a sender. We will often refer to these as “drafts” which are displayed on the sender’s side.
4. We assume the recipient of messages is the one who can specify the number of messages they want delivered. We refer to undelivered messages as “inbox messages” and delivered messages as “downloaded messages.”



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

Manual tests were conducted by simulating 2+ clients and a server on three terminals for a single computer.  These manual tests also replicated on two computers to ensure proper scaling.

Automatic tests were placed in the tests/ directory.  Unit tests were written and conducted to test individual process requests and compare against our expected results. We used unittest which is natively built into Python, and we used its patch and MagicMock modules to mock responses from the SQL database and connections. We wrote a couple tests for each functionality, each accomplishing the following:

1. Successful and unsuccessful account failure (username already exists)
2. Successful login
3. Sending a message
4. Downloading a message
5. Checking a message (checkmark as read/unread and save that data)
6. Adding a new draft
7. Saving all drafts
8. Successful logout
9. Successful deletion of an account
10. Getting the user’s password
11. Receiving a message successfully and unsuccessfully

To execute the tests, run in tests/ the following terminal command: `python3 tests_rpc.py`

-------------------------------------------
## Code Cleanliness

To ensure code cleanliness, we adhered to the code structure as articulated in an earlier section.  We also did the following:
1. For tests_rpc.py, server.py, and chat_client.py, we instantiated them as classes.
2. For all functions in tests_rpc.py, server.py, chat_client.py, and gui.py, we put comments under each function header to help readers understand its implementation.
3. For gui.py, because we did not use a class but rather a set of functions, we made comments more robust beyond just header functions by utilizing sectioning-comments to "divide and sort" the functions based on usage.  For example, we have sections for logging in, logging out or deleting accounts, receiving messages in real time ("event listeners"), GUI loading frames, GUI loading features on existing frames, and GUI frame button-handling (if a button is clicked, for example).
4. For gui.py, we did the same "divide and sort" sectioning for variables.  We have sections for GUI variables and client data variables.






