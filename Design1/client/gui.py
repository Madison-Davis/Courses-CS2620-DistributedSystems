# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import client_conn
import database_functions as db



# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Vars: User's Data
"""
What should we keep track of?
client info:
username
password
all account usernames

client's drafts: 
# of drafts
messages
recipients
individual chechmarks
T/F: checkmark all of them

client's msgs: 
inbox msgs (the queue)
unread msgs
read msgs
"""
drafts_msgs             = {}        # dynamic: all of our drafts' current message entries
drafts_recipients       = {}        # dynamic: all of our drafts' current recipients
drafts_checkmarks       = {}        # dynamic: all of our drafts' individual checkmarks
drafts_all_checkmarked  = False     # T/F: do we want to send all the drafts?
num_drafts              = 0         # num of messages we're currently drafting to be sent

msgs_read               = {"User1":"Message1", "User2":"Message2", "User3":"Message3"}  # msgs in 'read' part of frame
msgs_unread             = {"User1":"Message1", "User2":"Message2", "User3":"Message3"}  # msgs in 'unread' part of frame
msgs_queue              = {}                                                            # msgs yet to be open in inbox queue

login_password          = None
login_username          = None
accounts                = [str(val) for val in range(100)] # TODO, placeholder



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
incoming_cols = [col_incoming_delete, col_incoming_checkbox, col_incoming_message, col_incoming_message]



# ++++++++++ Helper Functions: Login/Logout ++++++++++ #

def check_username(username):
    """ Determines if it is a returning user and responds accordingly.
    Regardless if new or old, provides place for password.
    Gives different textual response based if new/returning."""
    global login_password
    username = username.get()
    # TODO: UNCOMMENT
    # account_users, accounts_pwds = client_conn.client_conn_list_accounts()
    account_users = []
    account_pwds = []
    result_text = "Welcome Back!" if username in account_users else "Welcome, New User!"
    new_user = False if username in account_users else True
    # Create password label and entry
    tk.Label(login_frame, text=result_text).grid(row=3, column=0, padx=5)
    tk.Label(login_frame, text="Password:").grid(row=4, column=0, padx=5)
    login_password = tk.Entry(login_frame, show='*')
    login_password.grid(row=5, column=0, padx=5)
    # Create enter button
    tk.Button(login_frame, text="Enter", command=lambda:login(new_user, account_users, account_pwds)).grid(row=6, column=0, padx=5)

def login(new_user, account_users, account_pwds):
    """ If new user, create an account.
    If returning user, verify correct username/password.
    Determine if good login, and if so, load main frame. """
    user = login_username.get()
    pwd = login_password.get()
    # If new user, create a new account
    if new_user:
        # TODO: UNCOMMENT
        #status = client_conn_create_account(user, pwd)
        #if not status:
        #    messagebox.showerror("Error", "Unable to create new user.  Try again")
        print("Created account!")
        user_data = []
    # If existing user, verify password lines up
    elif account_pwds[account_users.index(user)] != pwd:
        messagebox.showerror("Error", "Invalid Username or Password")
    # If existing user and password lines up, login/load information
    else:
        # TODO: UNCOMMENT
        # user_data = client_conn_login(user, pwd) # [inboxCount, msgs, drafts]
        pass
    login_frame.pack_forget()
    load_main_frame(user_data)
    main_frame.pack(fill='both', expand=True)
        
def logout():
    """ Default message template and return to login frame. """
    load_main_frame()
    main_frame.pack_forget()
    login_frame.pack(fill='both', expand=True)



# ++++++++++ Helper Functions: Main Page Buttons ++++++++++ #

def clicked_open_inbox(num, queue):
    """ When we click 'Open Inbox', we select 'num' of msgs in queue. """
    for i in range(num):
        # TODO: call '' on the msg
        create_new_unread_msg()
        continue

def clicked_msg_checkbox(check_var, btn, user, msgId):
    """ When we click 'Read/Unread' checkbox, update database and config."""
    # TODO: UNCOMMENT
    # client_conn.client_conn_check_message(user, msgId)
    btn.config(text="Read") if check_var.get() == 1 else btn.config(text="Unread")

def clicked_edit(row):
    """ When we click 'Edit' button, draft is editable. """
    drafts_msgs[row].config(state=tk.NORMAL)
    drafts_msgs[row].focus()

def clicked_saved(row):
    """ When we click 'Saved' button, draft is not editable. """
    drafts_msgs[row].config(state=tk.DISABLED)

def clicked_select_all():
    """ When we click 'Select all' button, turn on/off all checkboxes. """
    global drafts_all_checkmarked
    drafts_all_checkmarked = not drafts_all_checkmarked
    for i in drafts_checkmarks:
        drafts_checkmarks[i].set(drafts_all_checkmarked)

def clicked_new_button():
    """ When we click 'New' button, create a new draft """
    global num_drafts 
    num_drafts = create_new_draft(num_drafts)

def filter_recipients(event, row):
    """ Filters recipient dropdown list as user types. """
    typed_text = drafts_recipients[row].get().lower()
    filtered_users = [user for user in accounts if typed_text in user.lower()]
    drafts_recipients[row]['values'] = filtered_users   # Update dropdown options
    drafts_recipients[row].event_generate('<Down>')     # Open dropdown after filtering

def clicked_delete_msg(widget, user, msgId):
    """ When we click 'Delete' button, removes row and moves other rows up. """
    # TODO: UNCOMMENT
    # status = client_conn.client_conn_delete_message(user, msgId)
    #if status != "ok":
    #    messagebox.showerror("Error", "Deletion unsuccessful")
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

def create_new_draft(num_drafts):
    """ Creates a new draft
        num_drafts: how many drafts do we currently have """
    i = num_drafts + start_row_drafts # the row we will put this new draft on
    # select button
    drafts_checkmarks[i] = tk.BooleanVar() # unique to each row
    tk.Checkbutton(main_frame, variable=drafts_checkmarks[i]).grid(row=i+1, column=col_sending_checkbox, padx=5, pady=5)
    # deliverable's message box
    tk.Frame(main_frame, width=2, height=25, bg='black').grid(row=i+1, column=col_sending_message, padx=2, pady=5, sticky='ns')
    message_entry = tk.Entry(main_frame, width=30, state=tk.DISABLED)
    message_entry.grid(row=i+1, column=col_sending_message, padx=5, pady=5)
    drafts_msgs[i] = message_entry
    # edit and save buttons
    tk.Button(main_frame, text="Edit", command=lambda r=i: clicked_edit(r)).grid(row=i+1, column=col_sending_edit)
    tk.Button(main_frame, text="Save", command=lambda r=i: clicked_saved(r)).grid(row=i+1, column=col_sending_save, padx=5)
    # recipient dropdown list
    recipient_entry = ttk.Combobox(main_frame, width=20, height=2)
    recipient_entry['values'] = accounts
    recipient_entry.set("Type or select...")
    recipient_entry.grid(row=i+1, column=col_sending_recipient, padx=5, pady=5)
    drafts_recipients[i] = recipient_entry
    # bind key release event to filter recipient dropdown
    recipient_entry.bind('<KeyRelease>', lambda event, r=i: filter_recipients(event, r))
    # update the number of drafts we currently have
    return num_drafts + 1

def create_new_unread_msg():
    pass



# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #

def load_login_frame():
    global login_username, login_password
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

def load_main_frame(user_data=[]):
    """ Clears and resets the main frame to its initial state. 
        user_data: user data to populate fields
        if user is None, then just provides defalt template."""
    # Part 0: Destroy Initial Widget
    for widget in main_frame.winfo_children():
        widget.destroy()
    # Part 1: Account Options
    tk.Button(main_frame, text="Logout", command=logout).grid(row=0, column=1, sticky="e", padx=5)
    tk.Button(main_frame, text="Delete Account", bg="red").grid(row=0, column=2, sticky="e", padx=5)
    # Part 2: Column and Sub-Column Titles For Receiving Messages
    tk.Label(main_frame, text="Receiving Messages", font=("Arial", 12, "bold"), width=20).grid(row=1, column=col_incoming_message, padx=5, pady=5)
    tk.Label(main_frame, text="Inbox", font=("Arial", 12, "bold"), width=30).grid(row=4, column=col_incoming_message, padx=5, pady=5)
    tk.Label(main_frame, text=f"Incoming: {15} Items", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_incoming_message, padx=5, pady=5)
    # Part 2.5: Open Inbox
    inbox_control_frame = tk.Frame(main_frame)
    inbox_control_frame.grid(row=3, column=col_incoming_message, sticky="ew")
    view_options = [5, 10, 15, 20, 25, 50]
    selected_val = tk.IntVar(value=5)
    tk.OptionMenu(inbox_control_frame, selected_val, *view_options, command=lambda value: selected_val.set(value)).pack(side="right")
    tk.Button(inbox_control_frame, text="Open Inbox Items", command=clicked_open_inbox(selected_val.get(), msgs_queue)).pack(side="right")
    # Part 3: Column and Sub-Column Titles for Sending Messages
    tk.Label(main_frame, text="Sending Messages", font=("Arial", 12, "bold"), width=30).grid(row=1, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Content", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Recipient", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_recipient, padx=5, pady=5)
    tk.Label(main_frame, text="Send", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_sending_checkbox, padx=5, pady=5)
    tk.Button(main_frame, text="Select All", command=clicked_select_all).grid(row=3, column=col_sending_checkbox, pady=10)
    tk.Button(main_frame, text="New", command=clicked_new_button).grid(row=3, column=col_sending_edit, pady=10)
    
    # TODO: delete these instantiations later on
    global drafts_checkmarks, drafts_msgs, drafts_recipients, num_drafts
    drafts_checkmarks   = {}
    drafts_msgs         = {}
    drafts_recipients   = {}
    num_drafts          = 0
    user_data = ["dummy stuff"]

    if user_data != []:
        load_main_frame_user_info(user_data)

def load_main_frame_user_info(user_data):
    """ Clears and resets the main frame to its initial state. 
        user: name of user to populate fields with data 
        if user is None, then wipe data/nothing there"""
    
    # TODO: parse through user_data to get relevant info... for now im using dummy data
        #inboxCount = user_data[0]
        #msgs = user_data[1]
        #drafts = user_data[2]
        # dummy example of what parsed should look like:
    parsed_user_data = [1,
    [["user",1,"User1","hello!",0,0],
     ["user",2,"User2","hello!",0,0]], 
     [["user",1,"User1","send to User1!"],
     ["user",1,"","send to whoever!"]]] 

    # Customize "Incoming Messages" Column
    # Populate messages
    for i, msg in enumerate(parsed_user_data[1]): 
        # Is it meant to be in inbox?  Otherwise, make a widget
        if msg[-1] != 1:
            sender = msg[2]
            checkbox = msg[4]
            content = msg[3]
            user = msg[0]
            msgId = msg[1]

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


# ++++++++++++++  Main Function  ++++++++++++++ #

# Create Main GUI By Starting Up Login Frame
load_login_frame()
gui.mainloop()

