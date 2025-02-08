# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import tkinter as tk
import uuid
from tkinter import messagebox, ttk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import client_conn



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
start_row_drafts        = 4
incoming_cols = [col_incoming_delete, col_incoming_checkbox, 
                 col_incoming_message, col_incoming_message]



# ++++++++++ Helper Functions: Login/Logout ++++++++++ #

def check_username(username):
    """ Determines if it is a returning user and responds accordingly.
    Regardless if new or old, provides place for password.
    Gives different textual response based if new/returning."""
    global login_username, login_pwd, db_user_data, db_accounts
    username = username.get()
    # NOTE: should not pull passwords for security
    account_users = client_conn.client_conn_list_accounts()
    pwd_hash = client_conn.client_conn_get_pwd(username)
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
    # If new user, create a new account
    if new_user:
        status = client_conn.client_conn_create_account(user, pwd)
        if not status:
           messagebox.showerror("Error", "Unable to create new user.  Try again")
        db_user_data = [0,[],[],[]]
    # If existing user, verify password lines up
    elif pwd_hash != pwd:
        messagebox.showerror("Error", "Invalid Username or Password")
    # If existing user and password lines up, login/load information
    else:
        db_user_data = client_conn.client_conn_login(user, pwd) # [inboxCount, old_msgs, inbox_msgs, drafts]
    login_frame.pack_forget()
    load_main_frame(db_user_data)
    main_frame.pack(fill='both', expand=True)
        
def logout():
    """ Default message template and return to login frame. """
    status = client_conn.client_conn_logout(login_username)
    if not status:
       messagebox.showerror("Error", "Unable to log out.")
    # Save all drafts to db
    drafts = [(msg[2], msg[3]) for msg in db_user_data[3]]
    client_conn.client_conn_save_drafts(login_username, drafts)
    load_main_frame()
    main_frame.pack_forget()
    load_login_frame()

def delete_account():
    """ Delete account and send request to DB to update this. """
    # Reset all data
    db_accounts = []
    db_user_data = [0, [], [], []]
    status = client_conn.client_conn_delete_account(login_username, login_pwd)
    if not status:
       messagebox.showerror("Error", "Unable to delete user.")
    load_main_frame()
    main_frame.pack_forget()
    load_login_frame()


# ++++++++++ Helper Functions: Main Page Buttons ++++++++++ #

def clicked_send():
    """ When we click 'Send', we send all drafts with checks and delete from GUI. """
    # Get user drafts that have checkmarks from GUI
    drafts = db_user_data[3]
    drafts_with_checkmarks = [msg for msg in drafts if msg[-1] == 1]
    # Go through the drafts and send them one by one
    for draft in drafts_with_checkmarks:
        recipient = draft[2]
        content = draft[3]
        status = client_conn.client_conn_send_message(recipient, login_username, content)
        if status != "ok":
           messagebox.showerror("Error", "Delivery of some messages unsuccessful")
        # Remove drafts that are sent
        db_user_data.remove(draft) # can you directly move an item of a sublist?

def clicked_open_inbox(num):
    """ When we click 'Open Inbox', we select 'num' of msgs in queue. """
    # Get all messages in inbox (if the inbox is marked as True)
    inbox_msgs = db_user_data[2]
    inboxCount = len(inbox_msgs)
    # Go through 'num' messages, create a new unread msg, and remove from inbox db
    for i in range(num):
        # Edge case: user asks for too many
        if i >= inboxCount:
            messagebox.showerror("Error", message="Nothing in inbox!")
            break
        create_new_unread_msg(inbox_msgs[i])
        client_conn.client_conn_download_message(login_username, inbox_msgs[i][0])  # does this store message ID?
        db_user_data.remove(inbox_msgs[i])  # can you directly move an item of a sublist?

def clicked_msg_checkbox(check_var, btn, user, msgId):
    """ When we click 'Read/Unread' checkbox, update database and config."""
    client_conn.client_conn_check_message(user, msgId)
    btn.config(text="Read") if check_var.get() == 1 else btn.config(text="Unread")

def clicked_edit(row):
    """ When we click 'Edit' button, draft is editable. """
    drafts_msgs[row].config(state=tk.NORMAL)
    drafts_msgs[row].focus()

def clicked_saved(row, draftId, msg, recipient, checked):
    """ When we click 'Saved' button, draft is not editable. 
    Update server DB with new information."""
    global db_user_data
    drafts_msgs[row].config(state=tk.DISABLED)
    # We already made a new draft when clicking 'New', so let's just find that entry
    data_index = -1
    for i, entry in enumerate(db_user_data[3]):
        if entry[0] == draftId:
            data_index = i
            break
    if data_index == -1:
        messagebox.showerror("Error", "Unable to save.")
    # Once we have entry, update its values
    db_user_data[3][data_index][2] = recipient
    db_user_data[3][data_index][3] = msg
    db_user_data[3][data_index][4] = checked
    # When we're ready to send, we'll use this data to format our JSON!

def clicked_select_all():
    """ When we click 'Select all' button, turn on/off all checkboxes. """
    global drafts_all_checkmarked
    drafts_all_checkmarked = not drafts_all_checkmarked
    for i in drafts_checkmarks:
        drafts_checkmarks[i].set(drafts_all_checkmarked)

def clicked_new_button():
    """ When we click 'New' button, create a new draft """  
    row_idx = len(db_user_data[3]) + start_row_messages
    create_new_draft(row_idx)

def filter_recipients(event, row):
    """ Filters recipient dropdown list as user types. """
    typed_text = drafts_recipients[row].get().lower()
    updated_accounts = client_conn.client_conn_list_accounts()
    filtered_users = [user for user in updated_accounts if typed_text in user.lower()]
    drafts_recipients[row]['values'] = filtered_users   # Update dropdown options
    drafts_recipients[row].event_generate('<Down>')     # Open dropdown after filtering

def clicked_delete_msg(widget, user, msgId):
    """ When we click 'Delete' button, removes row and moves other rows up. """
    status = client_conn.client_conn_delete_message(user, msgId)
    if status != "ok":
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
        num_drafts: how many drafts do we currently have
        draftId: assigns unique draftId to this draft for the user."""
    global db_user_data
    draftId = uuid.uuid4()
    i = row_idx # start here
    # create the select button
    drafts_checkmarks[i] = tk.BooleanVar() # unique to each row
    tk.Checkbutton(main_frame, variable=drafts_checkmarks[i]).grid(row=i+1, column=col_sending_checkbox, padx=5, pady=5)
    # create deliverable's message box
    tk.Frame(main_frame, width=2, height=25, bg='black').grid(row=i+1, column=col_sending_message, padx=2, pady=5, sticky='ns')
    message_entry = tk.Entry(main_frame, width=30, state=tk.DISABLED)
    message_entry.grid(row=i+1, column=col_sending_message, padx=5, pady=5)
    drafts_msgs[i] = message_entry
    # create recipient dropdown list
    recipient_entry = ttk.Combobox(main_frame, width=20, height=2)
    recipient_entry['values'] = db_accounts
    recipient_entry.set(recipient_entry)
    recipient_entry.grid(row=i+1, column=col_sending_recipient, padx=5, pady=5)
    drafts_recipients[i] = recipient_entry
    # bind key release event to the filter recipient dropdown
    recipient_entry.bind('<KeyRelease>', lambda event, r=i: filter_recipients(event, r))
    # create edit and save buttons
    tk.Button(main_frame, text="Edit", command=lambda r=i: clicked_edit(r)).grid(row=i+1, column=col_sending_edit)
    save_btn = tk.Button(main_frame, text="Save")
    save_btn.config(command=lambda r=i: clicked_saved(r, draftId, drafts_msgs[i].get(), drafts_recipients[i].get(), drafts_checkmarks[i].get()))
    save_btn.grid(row=i+1, column=col_sending_save, padx=5)
    # create draftId for this draft
    # return num of drafts and draftId
    db_user_data[3].append([draftId, login_username, "", "", 0])

def create_existing_draft(row_idx, draftId, recipient="", msg="", checked=0):
    """ Creates a pre-existing draft
        num_drafts: how many drafts do we currently have
        draftId: assigns unique draftId to this draft for the user."""
    i = row_idx + start_row_drafts # start here
    # create the select button
    drafts_checkmarks[i] = tk.BooleanVar() # unique to each row
    tk.Checkbutton(main_frame, variable=drafts_checkmarks[i]).grid(row=i+1, column=col_sending_checkbox, padx=5, pady=5)
    # create deliverable's message box
    tk.Frame(main_frame, width=2, height=25, bg='black').grid(row=i+1, column=col_sending_message, padx=2, pady=5, sticky='ns')
    message_entry = tk.Entry(main_frame, width=30, state=tk.NORMAL)
    message_entry.grid(row=i+1, column=col_sending_message, padx=5, pady=5)
    message_entry.insert(0, msg)
    message_entry.config(state=tk.DISABLED)
    drafts_msgs[i] = message_entry
    # create recipient dropdown list
    recipient_entry = ttk.Combobox(main_frame, width=20, height=2)
    recipient_entry['values'] = db_accounts
    recipient_entry.set(recipient)
    recipient_entry.grid(row=i+1, column=col_sending_recipient, padx=5, pady=5)
    drafts_recipients[i] = recipient_entry
    # bind key release event to the filter recipient dropdown
    recipient_entry.bind('<KeyRelease>', lambda event, r=i: filter_recipients(event, r))
    # create edit and save buttons
    tk.Button(main_frame, text="Edit", command=lambda r=i: clicked_edit(r)).grid(row=i+1, column=col_sending_edit)
    save_btn = tk.Button(main_frame, text="Save")
    save_btn.config(command=lambda r=i: clicked_saved(r, draftId, drafts_msgs[i].get(), drafts_recipients[i].get(), drafts_checkmarks[i].get()))
    save_btn.grid(row=i+1, column=col_sending_save, padx=5)

def create_new_unread_msg(inbox_msg):
    """ Create new unread message when opening inbox, shifting everything else down by 1."""
    # Set up variables
    sender = inbox_msg[2]
    checkbox = 0 # default
    content = inbox_msg[3]
    user = inbox_msg[1]
    msgId = inbox_msg[0]
    i = start_row_messages
    next_row = i + 1
    # Shift down all rows by 1 to make room for inserted widget
    widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]
    while widgets_below:
        for widget in widgets_below:
            grid_info = widget.grid_info()
            if int(grid_info["column"]) in incoming_cols:
                widget.grid(row=grid_info["row"] - 1)   
        next_row += 1
        widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]
    # Insert new widget
    checkbox_text = "Read" if checkbox else "Unread"
    msg_formatted = sender + ": " + content
    btn_del = tk.Button(main_frame, text="Delete")
    btn_del.grid(row=i+1, column=col_incoming_delete)
    btn_del.config(command=lambda widget=btn_del: clicked_delete_msg(widget, user, msgId))
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

def load_main_frame_user_info(db_user_data):
    """ Clears and resets the main frame to its initial state. 
        user: name of user to populate fields with data 
        if user is None, then wipe data/nothing there"""
    # Customize "Incoming Messages" Column
    # Populate messages
    for i, msg in enumerate(db_user_data[1]): 
        # user, msgId, sender user, msg, checked, inbox
        # db_user_data[1] are non-inbox messages
        sender = msg[2]
        checkbox = msg[4]
        content = msg[3]
        user = msg[1]
        msgId = msg[0]
        checkbox_text = "Read" if checkbox else "Unread"
        i = i + start_row_messages
        msg_formatted = sender + ": " + content
        btn_del = tk.Button(main_frame, text="Delete")
        btn_del.grid(row=i+1, column=col_incoming_delete)
        btn_del.config(command=lambda widget=btn_del: clicked_delete_msg(widget, user, msgId))
        check_var = tk.IntVar()
        check_btn = tk.Checkbutton(main_frame, text=checkbox_text, variable=check_var)
        check_btn.config(command=lambda var=check_var, btn=check_btn: clicked_msg_checkbox(var, btn, user, msgId))
        check_btn.grid(row=i+1, column=col_incoming_checkbox)
        check_btn.var = check_var # saves a reference to allow us to immediately check it
        check_var.set(checkbox)
        tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)
    i = 0
    for draft in db_user_data[3]: 
        print(draft)
        create_existing_draft(i, draft[1], draft[2], draft[3], draft[4])
        i += 1



# ++++++++++++++  Main Function  ++++++++++++++ #

# Create Main GUI By Starting Up Login Frame
load_login_frame()
gui.mainloop()

