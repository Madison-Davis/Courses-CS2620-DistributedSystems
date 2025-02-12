# gui.py



# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import client_conn
import client_conn_custom
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config")))
import config
import threading
import hashlib



# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Vars: User's Data
"""
SQL DB Setup: 3 databases
Accounts database: uuid, user, pwd, logged_in
Msgs     database: msg_id, user, sender, msg, checked, inbox
Drafts   database: draft_id, user, recipient, msg, checked
"""
# These are for retrieving information from DB, as well as 
# creating edits/changes that we'll send to the DB.

# list of account usernames, updated to/from DB
db_accounts             = []

# list of all (un)downloaded and drafted msgs, updated to/from DB
# # inboxCount
# # old_msgs: msg_id, user, sender, msg, checked, inbox
# # inbox_msgs: msg_id, user, sender, msg, checked, inbox
# # drafts: draft_id, user, recipient, msg, checked
db_user_data            = [0, 
                           [],
                           [],
                           []]
                                    # NOTE: we will take this and update it on our side
                                    # then, when we send over this data to server, SQL will:
                                        # DB data: select ALL from DB
                                        # determine rows to delete: DB data - modified data
                                        # determine rows to insert: modified data row if row not in DB data
                                        # determine rows to update: for each row, val in DB: see if cell = modified data cell

# These are for edits we make to the drafts, but are yet to be "queued" up for DB 
# For example, we can edit a message as many times as we want, but only when we save do we
# edit our db_user_data to reflect the changes.
# when do we solidify the draft changes: 'new' button, 'save' button
drafts_msgs             = {}        # dynamic: all of our drafts' current message entries
drafts_recipients       = {}        # dynamic: all of our drafts' current recipients
drafts_checkmarks       = {}        # dynamic: all of our drafts' individual checkmarks
drafts_all_checkmarked  = False     # T/F: do we want to send all the drafts?
login_username          = None
login_pwd               = None



# +++++++++++++++  Variables: GUI  +++++++++++++++ #

# Vars: TK Frames We Use
gui = tk.Tk()
gui.title("Login")
gui.geometry("1400x600")
login_frame = tk.Frame(gui)
main_frame = tk.Frame(gui)

# Vars: TK Column-Positioning
"""
[Incoming Messages]
1: delete
2: checkbox (on = read, off = unread)
3: message
[Sending Messages]
4: send checkbox
5: message
6: edit
7: save
8: recipient
"""
col_incoming_delete     = 1
col_incoming_checkbox   = 2
col_incoming_message    = 3
col_sending_checkbox    = 4
col_sending_message     = 5
col_sending_edit        = 6
col_sending_save        = 7
col_sending_recipient   = 8
start_row_messages      = 5
start_row_drafts        = 5
incoming_cols = [col_incoming_delete, col_incoming_checkbox, 
                 col_incoming_message, col_incoming_message]
sending_cols = [col_sending_checkbox, col_sending_message, 
                 col_sending_edit, col_sending_save,
                 col_sending_recipient]


# ++++++++++ Helper Functions: Security ++++++++++ #

def hash_password(password: str) -> str:
    """Hashes a password with a randomly generated salt using SHA-256."""
    salt = os.urandom(16)  # Generate a 16-byte salt
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + ":" + hashed_password.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against a stored hash."""
    salt, hashed_password = stored_hash.split(":")
    salt = bytes.fromhex(salt)
    new_hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return new_hashed_password.hex() == hashed_password


# ++++++++++ Helper Functions: Login/Logout ++++++++++ #

def check_username(username):
    """ Determines if it is a returning user and responds accordingly.
    Regardless if new or old, provides place for password.
    Gives different textual response based if new/returning."""
    global login_username, login_pwd, db_user_data, db_accounts
    username = username.get()
    # NOTE: should not pull passwords for security
    if config.PROTOCOL == 0:
        account_users = client_conn.client_conn_list_accounts()
        pwd_hash = client_conn.client_conn_get_pwd(username)
    else:
        account_users = client_conn_custom.client_conn_list_accounts()
        pwd_hash = client_conn_custom.client_conn_get_pwd(username)
    result_text = "Welcome Back!" if username in account_users else "Welcome, New User!"
    new_user = False if username in account_users else True
    # Create password label and entry
    tk.Label(login_frame, text=result_text).grid(row=3, column=0, padx=5)
    tk.Label(login_frame, text="Password:").grid(row=4, column=0, padx=5)
    login_pwd = tk.Entry(login_frame, show='*')
    login_pwd.grid(row=5, column=0, padx=5)
    # Create enter button
    tk.Button(login_frame, text="Enter", command=lambda:login(new_user, account_users, pwd_hash)).grid(row=6, column=0, padx=5)

def login(new_user, account_users, pwd_hash):
    """ If new user, create an account.
    If returning user, verify correct username/password.
    Determine if good login, and if so, load main frame. """
    global login_username, login_pwd, db_user_data, db_accounts
    user = login_username.get()
    pwd = login_pwd.get()
    entered_pwd_hashed = hash_password(pwd)
    # If new user, create a new account
    if new_user:
        if config.PROTOCOL == 0:
            status = client_conn.client_conn_create_account(user, entered_pwd_hashed)
        else:
            status = client_conn_custom.client_conn_create_account(user, entered_pwd_hashed)
        if not status:
           messagebox.showerror("Error", "Unable to create new user.  Try again")
        db_user_data = [0,[],[],[]]
    # If existing user, verify password lines up
    elif not verify_password(pwd, pwd_hash):
        messagebox.showerror("Error", "Invalid Username or Password")
        return
    # If existing user and password lines up, login/load information
    else:
        if config.PROTOCOL == 0:
            db_user_data = client_conn.client_conn_login(user, pwd_hash) # [inboxCount, old_msgs, inbox_msgs, drafts]
        else:
            db_user_data = client_conn_custom.client_conn_login(user, pwd_hash)
    login_frame.pack_forget()
    load_main_frame(db_user_data)
    main_frame.pack(fill='both', expand=True)



# +++++++++++++ Helper Functions: Event Listener +++++++++++++ #

def update_inbox_callback(incoming_msg):
    """ Updates the GUI inbox dynamically when a new message arrives. """
    global db_user_data
    db_user_data[2].insert(0, incoming_msg)  # Insert into inbox
    db_user_data[0] += 1
    # Update inbox count
    update_inbox_count(len(db_user_data[2]))
    gui.after(100, load_main_frame, db_user_data)

def update_inbox_count(count):
    """ Update the GUI inbox count dynamically when a new message arrives. """
    for widget in main_frame.grid_slaves():
        if widget.grid_info()["row"] == 2 and widget.grid_info()["column"] == col_incoming_message:
            widget.destroy()
            break
    lbl_incoming = tk.Label(main_frame, text=f"Incoming: {count} Items", font=("Arial", 12, "bold"), width=30)
    lbl_incoming.grid(row=2, column=col_incoming_message, padx=5, pady=5)
    


# +++++++++++++ Helper Functions: GUI Update +++++++++++++ #

def logout():
    #client_conn.stop_message_listener_thread()
    #client_conn.stop_message_listener_thread()
    """ Default message template and return to login frame. """
    if config.PROTOCOL == 0:
        status = client_conn.client_conn_logout(login_username.get())
    else:
        status = client_conn_custom.client_conn_logout(login_username.get())
    if not status:
       messagebox.showerror("Error", "Unable to log out.")
    # Save all drafts to db
    if config.PROTOCOL == 0:
        client_conn.client_conn_save_drafts(login_username.get(), db_user_data[3])
    else:
        client_conn_custom.client_conn_save_drafts(login_username.get(), db_user_data[3])
    load_main_frame()
    main_frame.pack_forget()
    load_login_frame()

def delete_account():
    """ Delete account and send request to DB to update this. """
    # Reset all data
    global db_accounts, db_user_data
    db_accounts = []
    db_user_data = [0, [], [], []]
    if config.PROTOCOL == 0:
        status = client_conn.client_conn_delete_account(login_username.get())
    else:
        status = client_conn_custom.client_conn_delete_account(login_username.get())
    if not status:
       messagebox.showerror("Error", "Unable to delete user.")
    load_main_frame()
    main_frame.pack_forget()
    load_login_frame()



# ++++++++++ Helper Functions: Main Page Buttons ++++++++++ #

def clicked_send():
    """ When we click 'Send', we send all drafts with checks and delete from GUI. """
    global db_user_data, drafts_rows, drafts_msgs, drafts_checkmarks, drafts_recipients, drafts_all_checkmarked
    
    # Send one-by-one user drafts that have checkmarks
    drafts_with_checkmarks = [draft for i, draft in enumerate(db_user_data[3]) if drafts_checkmarks[i].get()]

    for draft in drafts_with_checkmarks:
        draft_id = draft["draft_id"]
        recipient = draft["recipient"]
        content = draft["msg"]
        if config.PROTOCOL == 0:
            msgId = client_conn.client_conn_send_message(draft_id, recipient, login_username.get(), content)
        else:
            msgId = client_conn_custom.client_conn_send_message(draft_id, recipient, login_username.get(), content)
        if not msgId:
           messagebox.showerror("Error", "Delivery of some messages unsuccessful")
           return

    # Delete all checked-drafts from GUI and move up remaining GUI items
    total_num_drafts = len(db_user_data[3])
    for row in range(start_row_drafts, start_row_drafts+total_num_drafts+1):
        for w in main_frame.grid_slaves():
            if w.grid_info()["row"] == row and w.grid_info()["column"] in sending_cols:
                w.destroy()

    # Delete all remaining drafts in the database
    db_user_data[3] = [draft for i, draft in enumerate(db_user_data[3]) if drafts_checkmarks[i].get() == False]
    drafts_rows = [key for key, var in drafts_checkmarks.items() if var.get()]
    drafts_msgs = {key: value for key, value in drafts_msgs.items() if key not in drafts_rows}
    drafts_checkmarks = {key: value for key, value in drafts_checkmarks.items() if key not in drafts_rows}
    drafts_recipients = {key: value for key, value in drafts_recipients.items() if key not in drafts_rows}

    # Re-load these drafts
    for row_idx in range(len(db_user_data[3])):
        recipient = db_user_data[3][row_idx]["recipient"]
        msg = db_user_data[3][row_idx]["msg"]
        checked = db_user_data[3][row_idx]["checked"]
        create_existing_draft(row_idx, recipient, msg, checked)

def clicked_open_inbox(num):
    """ When we click 'Open Inbox', we select 'num' of msgs in queue. """
    # Get all messages in inbox (if the inbox is marked as True)
    global db_user_data
    inbox_msgs = db_user_data[2]
    inboxCount = len(inbox_msgs)
    # Go through 'num' messages, create a new unread msg, and remove from inbox db
    for i in range(num):
        # Edge case: user asks for too many
        if i >= inboxCount:
            break
        create_new_unread_msg(db_user_data[2][0])
        if config.PROTOCOL == 0:
            client_conn.client_conn_download_message(login_username.get(), inbox_msgs[i]["msg_id"])
        else:
            client_conn_custom.client_conn_download_message(login_username.get(), inbox_msgs[i]["msg_id"])
        db_user_data[0] -= 1
        opened_msg = db_user_data[2][0]
        db_user_data[2] = db_user_data[2][1:]
        db_user_data[1].append(opened_msg)
    # Update the inbox Count automatically
    for w in main_frame.grid_slaves():
        if w.grid_info()["row"] == 2 and w.grid_info()["column"] == col_incoming_message:
            w.destroy()
            break
    lbl_incoming = tk.Label(main_frame, text=f"Incoming: {db_user_data[0]} Items", font=("Arial", 12, "bold"), width=30)
    lbl_incoming.grid(row=2, column=col_incoming_message, padx=5, pady=5)

def clicked_msg_checkbox(check_var, btn, user, msgId):
    """ When we click 'Read/Unread' checkbox, update database and config."""
    if config.PROTOCOL == 0:
        client_conn.client_conn_check_message(user, msgId)
    else:
        client_conn_custom.client_conn_check_message(user, msgId)
    btn.config(text="Read") if check_var.get() == 1 else btn.config(text="Unread")

def clicked_edit(row):
    """ When we click 'Edit' button, draft is editable. """
    drafts_msgs[row].config(state=tk.NORMAL)
    drafts_msgs[row].focus()

def clicked_saved(row, msg, recipient, checked):
    """ When we click 'Saved' button, draft is not editable. 
    Update server DB with new information."""
    global db_user_data
    drafts_msgs[row].config(state=tk.DISABLED)
    if row >= len(db_user_data[3]):
        messagebox.showerror("Error", "Unable to save.")
    # Once we have entry, update its values
    db_user_data[3][row]["recipient"] = recipient
    db_user_data[3][row]["msg"] = msg
    db_user_data[3][row]["checked"] = checked
    # When we're ready to send, we'll use this data to format our JSON!

def clicked_select_all():
    """ When we click 'Select all' button, turn on/off all checkboxes. """
    global drafts_all_checkmarked
    drafts_all_checkmarked = not drafts_all_checkmarked
    for i in drafts_checkmarks:
        drafts_checkmarks[i].set(drafts_all_checkmarked)

def clicked_new_button():
    """ When we click 'New' button, create a new draft """  
    row_idx = len(db_user_data[3])
    create_new_draft(row_idx)

def filter_recipients(event, row):
    """ Filters recipient dropdown list as user types. """
    typed_text = drafts_recipients[row].get().lower()
    if config.PROTOCOL == 0:
        updated_accounts = client_conn.client_conn_list_accounts()
    else:
        updated_accounts = client_conn_custom.client_conn_list_accounts()
    filtered_users = [user for user in updated_accounts if typed_text in user.lower()]
    drafts_recipients[row]['values'] = filtered_users   # Update dropdown options
    drafts_recipients[row].event_generate('<Down>')     # Open dropdown after filtering

def clicked_delete_msg(widget, msg):
    """ When we click 'Delete' button, removes row and moves other rows up. """
    user = msg["user"]
    msgId = msg["msg_id"]
    if config.PROTOCOL == 0:
        status = client_conn.client_conn_delete_message(user, msgId)
    else:
        status = client_conn_custom.client_conn_delete_message(user, msgId)
    if not status:
       messagebox.showerror("Error", "Deletion unsuccessful")
    # Delete specified cells that correspond to the message we want to delete
    row = widget.grid_info()["row"]
    for w in main_frame.grid_slaves():
        if w.grid_info()["row"] == row and w.grid_info()["column"] in incoming_cols:
            w.destroy()
    # Shift up all rows below the deleted row up by 1
    next_row = row + 1
    widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]
    while widgets_below:
        for widget in widgets_below:
            grid_info = widget.grid_info()
            if int(grid_info["column"]) in incoming_cols:
                widget.grid(row=grid_info["row"] - 1)   
        next_row += 1
        widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]



# ++++++++++ Helper Functions: Create New Components ++++++++++ #

def create_new_draft(row_idx):
    """ Creates a new draft
        num_drafts: how many drafts do we currently have"""
    global db_user_data
    i = row_idx # start here
    # create the select button
    drafts_checkmarks[i] = tk.BooleanVar() # unique to each row
    tk.Checkbutton(main_frame, variable=drafts_checkmarks[i]).grid(row=i+start_row_messages+1, column=col_sending_checkbox, padx=5, pady=5)
    # create deliverable's message box
    tk.Frame(main_frame, width=2, height=25, bg='black').grid(row=i+start_row_messages+1, column=col_sending_message, padx=2, pady=5, sticky='ns')
    message_entry = tk.Entry(main_frame, width=30, state=tk.DISABLED)
    message_entry.grid(row=i+start_row_messages+1, column=col_sending_message, padx=5, pady=5)
    drafts_msgs[i] = message_entry
    # create recipient dropdown list
    recipient_entry = ttk.Combobox(main_frame, width=20, height=2)
    recipient_entry['values'] = db_accounts
    recipient_entry.set("")
    recipient_entry.grid(row=i+start_row_messages+1, column=col_sending_recipient, padx=5, pady=5)
    drafts_recipients[i] = recipient_entry
    # bind key release event to the filter recipient dropdown
    recipient_entry.bind('<KeyRelease>', lambda event, r=i: filter_recipients(event, r))
    # create edit and save buttons
    tk.Button(main_frame, text="Edit", command=lambda r=i: clicked_edit(r)).grid(row=i+start_row_messages+1, column=col_sending_edit)
    save_btn = tk.Button(main_frame, text="Save")
    save_btn.config(command=lambda r=i: clicked_saved(r, drafts_msgs[i].get(), drafts_recipients[i].get(), drafts_checkmarks[i].get()))
    save_btn.grid(row=i+start_row_messages+1, column=col_sending_save, padx=5)
    # return num of drafts
    # TODO: SPECIFY DRAFT_ID
    if config.PROTOCOL == 0:
        draft_id = client_conn.client_conn_add_draft(login_username.get(), "", "", 0)
    else:
        draft_id = client_conn_custom.client_conn_add_draft(login_username.get(), "", "", 0)
    db_user_data[3].append({"draft_id": draft_id, "user": login_username.get(), "recipient": "", "msg": "", "checked": 0})

def create_existing_draft(row_idx, recipient="", msg="", checked=0):
    """ Creates a pre-existing draft
        num_drafts: how many drafts do we currently have"""
    i = row_idx # start here
    # create the select button
    drafts_checkmarks[i] = tk.BooleanVar() # unique to each row
    tk.Checkbutton(main_frame, variable=drafts_checkmarks[i]).grid(row=i+start_row_drafts+1, column=col_sending_checkbox, padx=5, pady=5)
    # create deliverable's message box
    tk.Frame(main_frame, width=2, height=25, bg='black').grid(row=i+start_row_drafts+1, column=col_sending_message, padx=2, pady=5, sticky='ns')
    message_entry = tk.Entry(main_frame, width=30, state=tk.NORMAL)
    message_entry.grid(row=i+start_row_drafts+1, column=col_sending_message, padx=5, pady=5)
    message_entry.insert(0, msg)
    message_entry.config(state=tk.DISABLED)
    drafts_msgs[i] = message_entry
    # create recipient dropdown list
    recipient_entry = ttk.Combobox(main_frame, width=20, height=2)
    recipient_entry['values'] = db_accounts
    recipient_entry.set(recipient)
    recipient_entry.grid(row=i+start_row_drafts+1, column=col_sending_recipient, padx=5, pady=5)
    drafts_recipients[i] = recipient_entry
    # bind key release event to the filter recipient dropdown
    recipient_entry.bind('<KeyRelease>', lambda event, r=i: filter_recipients(event, r))
    # create edit and save buttons
    tk.Button(main_frame, text="Edit", command=lambda r=i: clicked_edit(r)).grid(row=i+start_row_drafts+1, column=col_sending_edit)
    save_btn = tk.Button(main_frame, text="Save")
    save_btn.config(command=lambda r=i: clicked_saved(r, drafts_msgs[i].get(), drafts_recipients[i].get(), drafts_checkmarks[i].get()))
    save_btn.grid(row=i+start_row_drafts+1, column=col_sending_save, padx=5)

def create_new_unread_msg(inbox_msg):
    """ Create new unread message when opening inbox, shifting everything else down by 1."""
    # Set up variables
    sender = inbox_msg["sender"]
    checkbox = 0 # default
    content = inbox_msg["msg"]
    user = inbox_msg["user"]
    msgId = inbox_msg["msg_id"]
    i = start_row_messages
    last_row = max([int(widget.grid_info()["row"]) for widget in main_frame.grid_slaves()], default=i)
    # Move all widgets **bottom to top** to avoid overwriting
    for row in range(last_row, i - 1, -1):  # Start from bottom row
        widgets_in_row = [widget for widget in main_frame.grid_slaves(row=row)]
        for widget in widgets_in_row:
            grid_info = widget.grid_info()
            if int(grid_info["column"]) in incoming_cols:
                widget.grid(row=grid_info["row"] + 1)  # Move down

    # Insert new widget
    checkbox_text = "Read" if checkbox else "Unread"
    msg_formatted = sender + ": " + content
    btn_del = tk.Button(main_frame, text="Delete")
    btn_del.grid(row=i+1, column=col_incoming_delete)
    btn_del.config(command=lambda widget=btn_del: clicked_delete_msg(widget, inbox_msg))
    check_var = tk.IntVar()
    check_btn = tk.Checkbutton(main_frame, text="Unread", variable=check_var)
    check_btn.config(command=lambda var=check_var, btn=check_btn: clicked_msg_checkbox(var, btn, user, msgId))
    check_btn.grid(row=i+1, column=col_incoming_checkbox)
    check_btn.var = check_var # saves a reference to allow us to immediately check it
    check_var.set(checkbox)
    tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)


# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #

def load_login_frame():
    global login_username, login_pwd, login_frame
    # Destroy login frame if we're logging out/going back after changes
    if login_frame:
        login_frame.destroy()
        login_frame = tk.Frame(gui)
    login_frame.pack(fill='both', expand=True)
    # Part 0: dfine column/row weights
    weights = [10,1,1,1,1,1,1,10]
    for i in range(len(weights)):
        login_frame.rowconfigure(i, weight=weights[i]) 
    login_frame.columnconfigure(0, weight=1) 
    # Part 1: create username label and entry
    # use 'pack' to position relative to other items
    tk.Label(login_frame, text="Enter New or Existing Username:").grid(row=1, column=0, padx=5)
    login_username = tk.Entry(login_frame)
    login_username.grid(row=2, column=0, padx=5)
    # Part 2: determine if new/existing user
    login_username.bind('<Return>', lambda event,username=login_username: check_username(username))

def load_main_frame(db_user_data=[0,[],[],[]]):
    """ Clears and resets the main frame to its initial state. 
        db_user_data: user data to populate fields
        if user is None, then just provides defalt template."""
    # Part 0: Destroy Initial Widget
    for widget in main_frame.winfo_children():
        widget.destroy()

    global login_username
    greeting_label = tk.Label(main_frame, text=f"Hello, {login_username.get()}!", font=("Arial", 14, "bold"))
    greeting_label.grid(row=0, column=3, columnspan=3, padx=10, pady=10)

    # Part 1: Account Options
    tk.Button(main_frame, text="Logout", command=logout).grid(row=0, column=1, sticky="e", padx=5)
    tk.Button(main_frame, text="Delete Account", bg="red", command=delete_account).grid(row=0, column=2, sticky="e", padx=5)
    # Part 2: Column and Sub-Column Titles For Receiving Messages
    tk.Label(main_frame, text="Receiving Messages", font=("Arial", 12, "bold"), width=20).grid(row=1, column=col_incoming_message, padx=5, pady=5)
    tk.Label(main_frame, text="Inbox", font=("Arial", 12, "bold"), width=30).grid(row=4, column=col_incoming_message, padx=5, pady=5)
    tk.Label(main_frame, text=f"Incoming: {db_user_data[0]} Items", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_incoming_message, padx=5, pady=5)
    # Part 2.5: Open Inbox
    inbox_control_frame = tk.Frame(main_frame)
    inbox_control_frame.grid(row=3, column=col_incoming_message, sticky="ew")
    view_options = [5, 10, 15, 20, 25, 50]
    selected_val = tk.IntVar(value=5)
    tk.OptionMenu(inbox_control_frame, selected_val, *view_options, command=lambda value: selected_val.set(value)).pack(side="right")
    tk.Button(inbox_control_frame, text="Open Inbox Items", command=lambda:clicked_open_inbox(selected_val.get())).pack(side="right")
    # Part 3: Column and Sub-Column Titles for Sending Messages
    tk.Label(main_frame, text="Sending Messages", font=("Arial", 12, "bold"), width=30).grid(row=1, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Content", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Recipient", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_recipient, padx=5, pady=5)
    tk.Label(main_frame, text="Send", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_sending_checkbox, padx=5, pady=5)
    tk.Button(main_frame, text="Select All", command=clicked_select_all).grid(row=4, column=col_sending_checkbox, pady=10)
    tk.Button(main_frame, text="Send", command=clicked_send).grid(row=3, column=col_sending_checkbox, pady=10)
    tk.Button(main_frame, text="New", command=clicked_new_button).grid(row=3, column=col_sending_edit, pady=10)

    # blank out any unsaved changes to our drafts, as we're reloading this screen
    global drafts_checkmarks, drafts_msgs, drafts_recipients
    drafts_checkmarks   = {}
    drafts_msgs         = {}
    drafts_recipients   = {}

    if db_user_data != [0,[],[],[]]:
        load_main_frame_user_info(db_user_data)

    # Start listening for incoming messages with a callback
    # threading.Thread(target=client_conn.start_message_listener, args=(update_inbox_ui,), daemon=True).start()

def load_main_frame_user_info(db_user_data):
    """ Clears and resets the main frame to its initial state. 
        user: name of user to populate fields with data 
        if user is None, then wipe data/nothing there"""
    # Customize "Incoming Messages" Column
    # Populate messages
    for i, msg in enumerate(db_user_data[1]): 
        # user, msgId, sender user, msg, checked, inbox
        # db_user_data[1] are non-inbox messages
        sender = msg["sender"]
        checkbox = msg["checked"]
        content = msg["msg"]
        user = msg["user"]
        msgId = msg["msg_id"]
        checkbox_text = "Read" if checkbox else "Unread"
        i = i + start_row_messages
        msg_formatted = sender + ": " + content
        btn_del = tk.Button(main_frame, text="Delete")
        btn_del.grid(row=i+1, column=col_incoming_delete)
        btn_del.config(command=lambda widget=btn_del: clicked_delete_msg(widget, msg))
        check_var = tk.IntVar()
        check_btn = tk.Checkbutton(main_frame, text=checkbox_text, variable=check_var)
        check_btn.config(command=lambda var=check_var, btn=check_btn: clicked_msg_checkbox(var, btn, user, msgId))
        check_btn.grid(row=i+1, column=col_incoming_checkbox)
        check_btn.var = check_var # saves a reference to allow us to immediately check it
        check_var.set(checkbox)
        tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)
    i = 0
    for draft in db_user_data[3]: 
        if draft["msg"]:
            create_existing_draft(i, draft["recipient"], draft["msg"], draft["checked"])
        i += 1



# ++++++++++++++  Main Function  ++++++++++++++ #

if __name__ == "__main__":
    if config.PROTOCOL == 0:
        listener_thread = threading.Thread(target=client_conn.client_conn_receive_message, 
                                       args=(update_inbox_callback,),
                                       daemon=True)
    else:
        listener_thread = threading.Thread(target=client_conn_custom.client_conn_receive_message, 
                                       args=(update_inbox_callback,),
                                       daemon=True)
    listener_thread.start()
    load_login_frame()
    gui.mainloop()