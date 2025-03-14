# CS 2620 Design Exercise 1: Wire Protocols


To see the version written in Google Docs, visit [here](https://docs.google.com/document/d/1GXQrAyj79GTzeqagSdFr4_hKF2uppkP0Q7CNnq8aewQ/edit?usp=sharing).


-------------------------------------------
## Design Requirements

Simple, client-server chat application. 
GUI required.
Connection information as config.

1. Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.
2. Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.
3. List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.
4. Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.
5. Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.
6. Delete a message or set of messages. Once deleted messages are gone.
7. Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.


-------------------------------------------
## Assumptions
- We assume no requirements for persistent storage, that is, if the server shuts down and reboots, it does not need to keep the information it had prior to the shutdown.  
- We assume no grouping of messages.  In other words, messages are stand-alone with no history-attached, similar to a Gmail-styled application.
- We assume “undelivered messages” refers to messages that have yet to be delivered by a sender.  We will often refer to these as “drafts” which are displayed on the sender’s side.
- We assume the recipient of messages is the one who can specify the number of messages they want delivered. We refer to undelivered messages as “inbox messages” and delivered messages as “downloaded messages.”


-------------------------------------------
## Running 

### JSON Wire Protocol
- Make sure PROTOCOL is set to 0 in `config.py`
- Start server: `py .\server\server.py`
- Run GUI: `py .\client\gui.py`

### Custom Wire Protocol
- Make sure PROTOCOL is set to 1 in `config.py`
- Start server: `py .\server\server_custom.py`
- Run GUI: `py .\client\gui.py`


-------------------------------------------
## Testing
Automatic tests were grouped using the server and the client. Manual tests were also conducted by simulating 2+ clients and a server on three terminals for a single computer. These manual tests were replicated on two computers to ensure proper scaling.

Unit tests were written and conducted to test individual process requests and compare against our expected results.
We used unittest which is natively built into Python, and we used its patch and MagicMock modules to mock responses from the SQL database and connections.
We wrote a couple tests for each functionality, each accomplishing the following: 
- Create a mock connection and SQL cursor
- Create mock return values from the database requests
- Create a sample JSON or custom wire protocol request
- Send the request to the appropriate server to process the request
- Decode the response that is received from the server
- Assert that the received response is the same as what is expected

To execute the unit tests, run:
- JSON: `py .\tests\tests_json.py`
- Custom: `py .\tests\tests_custom.py`


-------------------------------------------
## Code Structure
client
- `/gui.py`				⇐ set up the GUI for the client to interact with
- `/client_conn.py`		⇐ funcs. to set up communication with server via JSON
- `/client_conn_custom.py` 	⇐ same as above, but for our custom protocol

server
- `/server.py`		⇐ listens, receives, and responds to requests via JSON and SQL
- `/server_custom.py`	⇐ same as above, but for our custom protocol, not JSON
- `/chat_database.db`	⇐ SQL for three databases: accounts, messages, and drafts
- `/server_security.py`  ⇐ for hashing security

config
- `/config.py`		⇐ set variables such as HOST/PORT and chosen wire protocol

tests
- `/tests_server.py`	⇐ verify server properly works
- `/tests_client.py`	⇐ verify client properly works


-------------------------------------------
## SQL Database

Format: [COLUMN]: [TYPE], [DEFAULT]

Accounts Database
- `uuid`: int, N/A (no default; should not be in DB)
- `user`: str, N/A (no default; should not be in DB)
- `pwd`: str, N/A (no default; should not be in DB)
- `logged_in`: bool, 0

Messages Database
- `msg_id`: int, N/A (no default; should not be in DB)
- `user`: str, N/A (no default; should not be in DB)
- `sender`: str, N/A (no default; should not be in DB)
- `msg`: str, N/A (no default; should not be in DB)
- `checked`: bool, 0
- inbox: bool, 1

Drafts Database
- `draft_id`: int, N/A (no default; should not be in DB)
- `user`: str, N/A (no default; should not be in DB)
- `recipient`: str, ""
- `msg`: str, ""
- `checked`: bool, 0


-------------------------------------------
## GUI Design
- Login Frame: provides entries for username input and password input, as well as a button to submit the information.  Initially, only the username entry is displayed.  Upon entering a name, the client makes a request to the server to determine if they are a new user or not.  This then displays the password input along with a textual message specific to whether the user is new (“Welcome, new user!”) or not (“Welcome back!”).  Upon entering the password and clicking enter, the user is brought to the main frame.  If the user is returning, additional data about past drafts or messages are displayed.
- Main Frame: The top area is reserved for a logout button, delete account button, and greeting message specifying the current username.  The rest of the area is split into two main sections: received messages and drafts.
    - Inbox: a title that states “inbox” with the number of emails currently in the inbox, and an “open inbox” button with a specification for the number of emails desired to be opened (this number can be edited by the user via a dropdown menu).  Upon clicking the button, new messages pop up at the top of the “messages” area.  Messages are sent to the inbox whenever a user receives a message.
    - Messages: rows of messages, where each message has a delete button, an unchecked mark/unread, and the message displayed as [Sender: Message].  Messages are sent here if they have already been opened but not deleted before logging out, or if the user is logged in and receives a new message. Messages can also be checked as read, which persist even if the user logs out and logs back in.
    - Drafts: A list of drafts yet to be sent, along with a “Send” button and “Select All” button.  Each draft contains a select button, an entry field to type in the message, edit button, save button, and a dropdown list for accounts.


-------------------------------------------
## Client Data
The server works with a SQL database, but the client also deals with local data.  The client deals with (1) caching the results of the SQL database as well as (2) keeping tabs on information that will eventually be sent back to the database to update, insert, or delete items in the database.  Specifically, for each client, the following data structures are used:
- `db_user_data`: used to hold information from the SQL database.  
    - `inboxCount`: the number of items in the inbox
    - `old_msgs`: all database entries of messages that have been downloaded and are shown visibly in the “Messages” section of the GUI.
    - `inbox_msgs`: all database entries of messages that have not been downloaded and are hidden in the “Inbox” section of the GUI.
    - `drafts`: all database entries of drafts that are shown visibly in the “Drafts” section of the GUI.
- `db_accounts`: used to hold account usernames from the SQL database.
- `drafts_XXX`: used for drafts.  Drafts are saved to the SQL database upon creation and can be edited when the user explicitly pushes “Save”.  We would like a complete list of all the drafts and their information at any given time, even if some are not meant to be sent to the server quite yet. These data structures accomplish this function of holding this information. Values are strings separated by commas, where their index represents the row they show up in in the GUI.
    - `drafts_msgs`: stores draft message content
    - `drafts_recipients`: stores draft message recipients
    - `drafts_checkmarks`: stores all draft messages that are checked to be sent


-------------------------------------------
## Password Security
To ensure password security, we store all password information as hashed passwords. We use a randomly generated salt using SHA-256 via hashlib to generate hashed passwords and verify hashes against user-inputted passwords.


-------------------------------------------
## Communication
- Creating an account: `createAccount`
    - Request parameters: username, password hash
    - Action: check that username doesn’t already exist, then insert user information into accounts table
- Log in to an account: `login`
    - Request parameters: username, password hash
    - Action: determine whether the username and password hash matches an existing account, set the user’s status to logged in, get user’s newly received messages in their inbox, get user’s old messages, get user’s drafts
- List accounts: `listAccounts`
    - Request parameters: none
    - Action: get list of all usernames currently in accounts table
- Read messages: `checkMessage`
    - Request parameters: username, message ID
    - Action: set message status to checked
- Delete a message: `deleteMessage`
    - Request parameters: username, message ID
    - Action: remove message from messages table
- Delete an account: `deleteAccount`
    - Request parameters: username, password hash
    - Action: delete user’s received messages, delete user’s drafts, delete user’s account information
- Log out: `logout`
    - Request parameters: username
    - Action: set user’s status to logged out
- Store drafts: `addDrafts`
    - Request parameters: username, list of recipient and content of each draft message
    - Action: delete all old drafts, insert all new drafts
- Download message from inbox to main page: `downloadMessage`
    - Request parameters: username, message ID
    - Action: updates inbox property to be 1
- Send a message to a recipient: `sendMessage`
    - Request parameters: username, sender username, message text content
    - Action: check if recipient exists, add message characteristics in messages table

We keep track of the sockets of all clients that are currently connected to the server, and if one user is trying to send a message to another user that is currently logged in, then we trigger a live message sending mechanism by sending the message information to the recipient’s socket.

In `client_conn.py`, we defined a function called `client_conn_receive_message`, which uses a selector to listen for incoming messages. If the received message is of type “receiveMessage,” then we call a method called update_inbox_callback to immediately update the recipient’s GUI and notify them of an incoming message by incrementing the counter on their inbox. 


-------------------------------------------
## Wire Protocols

### JSON
When `config.PROTOCOL = 0`, we use JSON and call server.py to start a server dedicated to JSON. JSON responses are made as a dictionary. We generally utilized the following structure, (in the code, this is in proper JSON format, but it is displayed here for understanding):

`{	 protocolVersion: #,
description: “ “,
	actions: {
		action_name_one: {
			request:	     	{ action:, data: }
			success_response: 	{ status:, msg:, data:}
error_response: 	{ status:, msg:, data:}
		}
action_name_two: {
			request:	     	{ action:, data: }
			success_response: 	{ status:, msg:, data:}
error_response: 	{ status:, msg:, data:}
		}
}`


### Custom
When `config.PROTOCOL = 1`, we use a custom wire protocol and call server_custom.py to start a server dedicated to this protocol.

We use a custom wire protocol format of a header and payload, which follows a big-endian network byte order.  Specifically, we use: 
- `struct.pack("!H I", message_type, len(payload_bytes))`
    - !: specifies big-endian network byte order
    - H: unsigned short (2 bytes, 16-bit integer)
    - I: unsigned int (4 bytes, 32-bit integer)
- The message type follows this encoding scheme:
    - 0x0001: Login
    - 0x0002: Send Message
    - 0x0003: Create Account
    - 0x0004: List Accounts
    - 0x0005: Get Password
    - 0x0006: Add Draft
    - 0x0007: Save Drafts
    - 0x0008: Check Message
    - 0x0009: Download Message
    - 0x000A: Delete Message
    - 0x000B: Delete Account
    - 0x000C: Logout
The payload contains the information needed to complete a request or desired to return in a response, and it has variable length. 
- Different pieces of information are colon-separated.
- Elements of a list are comma-separated.
- Key-value pairs in a dictionary are semicolon-separated.
- Keys and values in a dictionary are equal sign-separated.
