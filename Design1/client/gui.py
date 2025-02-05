# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import tkinter as tk
import sys
import os
from tkinter import messagebox, ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import database_functions as db

# +++++++++++++++++  Variables  +++++++++++++++++ #

# Message Frame Global Variables
drafts_msgs         = {}        # dynamic: all of our drafts' current message entries
drafts_recipients   = {}        # dynamic: all of our drafts' current recipients
drafts_checkmarks   = {}        # dynamic: all of our drafts' current checked to be sent
all_checkmarked     = False     # T/F: do we want to send all the drafts?
num_drafts          = 0         # num of messages we're currently drafting to be sent
read_messages       = {"User1":"Message1", "User2":"Message2", "User3":"Message3"}
unread_messages     = {"User1":"Message1", "User2":"Message2", "User3":"Message3"}
accounts            = [str(val) for val in range(100)] # TODO

# Vars to determine what goes in what column
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

# Vars to ensure data populates below column titles
start_row_messages      = 4
start_row_drafts        = 4



# ++++++++++ Helper Functions: Login/Logout ++++++++++ #

def login():
    """ Determine if good login, and if so, load main frame. """
    username = login_username.get()
    password = login_password.get()
    # TODO: verify the username and password are valid
    if username and password:
        # Create new user if this is a new user
        if db.db_get_user_data(username) is None:
            db.db_create_new_user(username, password)
        # Load new screen
        login_frame.pack_forget()
        main_frame.pack(fill='both', expand=True)
    else:
        messagebox.showerror("Error", "Invalid Username or Password")

def logout():
    """ Logs out the user and returns to login frame. """
    load_main_frame()
    main_frame.pack_forget()
    login_frame.pack(fill='both', expand=True)

def send_message(row):
    """ TODO """

def filter_recipients(event, row):
    """ Filters recipient dropdown list as user types. """
    typed_text = drafts_recipients[row].get().lower()
    filtered_users = [user for user in accounts if typed_text in user.lower()]
    drafts_recipients[row]['values'] = filtered_users  # Update dropdown options
    drafts_recipients[row].event_generate('<Down>')  # Open dropdown after filtering



# ++++++++++ Helper Functions: Main Page Buttons ++++++++++ #

def clicked_edit(row):
    """ When we click 'Edit' button, draft is editable. """
    drafts_msgs[row].config(state=tk.NORMAL)
    drafts_msgs[row].focus()

def clicked_saved(row):
    """ When we click 'Saved' button, draft is not editable. """
    drafts_msgs[row].config(state=tk.DISABLED)

def clicked_select_all():
    """ When we click 'Select all' button, turn on/off all checkboxes. """
    global all_checkmarked
    all_checkmarked = not all_checkmarked
    for i in drafts_checkmarks:
        drafts_checkmarks[i].set(all_checkmarked)

def clicked_new_button():
    """ When we click 'New' button, create a new draft """
    global num_drafts 
    num_drafts = create_new_draft(num_drafts)

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

def clicked_delete_msg(widget, cols):
    """ When we click 'Delete' button, removes row and moves other rows up. """
    # Delete specified cells that correspond to the message we want to delete
    row = widget.grid_info()["row"]
    for w in main_frame.grid_slaves():
        if w.grid_info()["row"] == row and w.grid_info()["column"] in cols:
            w.destroy()
    # Shift up all rows below the deleted row up by 1
    next_row = row + 1
    widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]
    while widgets_below:
        for widget in widgets_below:
            grid_info = widget.grid_info()
            if int(grid_info["column"]) in cols:
                widget.grid(row=grid_info["row"] - 1)   
        next_row += 1
        widgets_below = [widget for widget in main_frame.grid_slaves(row=next_row)]


# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #

def load_login_frame():
    pass

def load_main_frame(user=None):
    """ Clears and resets the main frame to its initial state. 
        user:   name of user to populate fields with data 
                if user is None, then wipe data/nothing there"""

    for widget in main_frame.winfo_children():
        widget.destroy()  # Remove all existing widgets

    # Recreate the default layout
    top_frame = tk.Frame(main_frame, bg="black", height=30)
    top_frame.grid(row=0, column=0, columnspan=6, sticky="ew")
    tk.Label(top_frame, text="Account Info", bg="black", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
    tk.Button(top_frame, text="Logout", bg="black", fg="white", command=logout).pack(side="right", padx=100)
    tk.Button(top_frame, text="Delete Account", bg="black", fg="white").pack(side="right", padx=10)

    # Recreate column titles
    tk.Label(main_frame, text="Incoming Messages", font=("Arial", 12, "bold"), width=20).grid(row=1, column=col_incoming_message, padx=5, pady=5)
    tk.Label(main_frame, text="Send Messages", font=("Arial", 12, "bold"), width=30).grid(row=1, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Content", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_message, padx=5, pady=5)
    tk.Label(main_frame, text="Recipient", font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_recipient, padx=5, pady=5)
    tk.Label(main_frame, text="Send", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_sending_checkbox, padx=5, pady=5)
    tk.Label(main_frame, text="Unread", font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_incoming_message, padx=5, pady=5)

    # Recreate buttons
    tk.Button(main_frame, text="Select All", command=clicked_select_all).grid(row=3, column=col_sending_checkbox, pady=10)
    tk.Button(main_frame, text="New", command=clicked_new_button).grid(row=3, column=col_sending_edit, pady=10)

    # Reinitialize global variables
    global drafts_checkmarks, drafts_msgs, drafts_recipients, num_drafts
    drafts_checkmarks   = {}
    drafts_msgs         = {}
    drafts_recipients   = {}
    num_drafts          = 0

    user_data = db.db_get_user_data(user)
    if user_data is not None:
        load_main_frame_user_info(user_data)


def load_main_frame_user_info(user_info):
    """ Clears and resets the main frame to its initial state. 
        user:   name of user to populate fields with data 
                if user is None, then wipe data/nothing there"""

    # Customize "Incoming Messages" Column
    # Part 1: unread messages
    cols = [col_incoming_delete, col_incoming_message, col_incoming_message]
    for i, sender in enumerate(unread_messages): 
        i = i + start_row_messages
        msg_formatted = sender + ": " + read_messages[sender]
        tk.Button(main_frame, text="Delete", command=lambda btn=tk.Button: clicked_delete_msg(btn, cols)).grid(row=i+1, column=col_incoming_delete)
        tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)
    # Part 2: read messages
    read_title_row = start_row_messages + len(unread_messages) + 1
    tk.Label(main_frame, text="Read", font=("Arial", 12, "bold"), width=30).grid(row=read_title_row, column=col_incoming_message, padx=5, pady=5)
    for i, sender in enumerate(read_messages): 
        i = i + read_title_row
        msg_formatted = sender + ": " + read_messages[sender]
        tk.Button(main_frame, text="Delete", command=lambda btn=tk.Button: clicked_delete_msg(btn, cols)).grid(row=i+1, column=col_incoming_delete)
        tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)


# ++++++++++++++  Main Function  ++++++++++++++ #


# Create Main GUI
gui = tk.Tk()
gui.title("Login")
gui.geometry("1400x600")


# Create Login Frame/Page
login_frame = tk.Frame(gui)
login_frame.pack(fill='both', expand=True)
# Part 1: create username label and entry
# use 'pack' to position relative to other items
tk.Label(login_frame, text="Username:").pack()
login_username = tk.Entry(login_frame)
login_username.pack()
# Part 2: create password label and entry
tk.Label(login_frame, text="Password:").pack()
login_password = tk.Entry(login_frame, show='*')
login_password.pack()
# Part 3: create enter button
tk.Button(login_frame, text="Enter", command=login).pack()


# Create Main Message Frame/Page, Top Part
main_frame = tk.Frame(gui)
# Part 1: Dark-Grey Account Info Frame
top_frame = tk.Frame(main_frame, bg="black", height=30)
top_frame.grid(row=0, column=0, columnspan=6, sticky="ew")  # Sticky to expand across the full width
tk.Label(top_frame,  text="Account Info", bg="black", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
tk.Button(top_frame, text="Logout", bg="black", fg="white", command=logout).pack(side="right", padx=100)
tk.Button(top_frame, text="Delete Account", bg="black", fg="white").pack(side="right", padx=10)                                                                                                                  
# Part 2: Column and Sub-Column Titles 
tk.Label(main_frame, text="Incoming Messages",       font=("Arial", 12, "bold"), width=20).grid(row=1, column=col_incoming_message, padx=5, pady=5)
tk.Label(main_frame, text="Send Messages",           font=("Arial", 12, "bold"), width=30).grid(row=1, column=col_sending_message, padx=5, pady=5)
tk.Label(main_frame, text="Content",                 font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_message, padx=5, pady=5)
tk.Label(main_frame, text="Recipient",               font=("Arial", 12, "bold"), width=20).grid(row=2, column=col_sending_recipient, padx=5, pady=5)
tk.Label(main_frame, text="Send",                    font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_sending_checkbox, padx=5, pady=5)
tk.Label(main_frame, text="Unread",                  font=("Arial", 12, "bold"), width=30).grid(row=2, column=col_incoming_message, padx=5, pady=5)
tk.Button(main_frame, text="Select All",             command=clicked_select_all).grid(row=3, column=col_sending_checkbox, pady=10)
tk.Button(main_frame, text="New",                    command=lambda: clicked_new_button()).grid(row=3, column=col_sending_edit, pady=10)


# Customize "Incoming Messages" Column
# Part 1: unread messages
cols = [col_incoming_delete, col_incoming_message, col_incoming_message]
for i, sender in enumerate(unread_messages): 
    i = i + start_row_messages
    msg_formatted = sender + ": " + read_messages[sender]
    btn = tk.Button(main_frame, text="Delete")
    btn.grid(row=i+1, column=col_incoming_delete)
    btn.config(command=lambda widget=btn: clicked_delete_msg(widget, cols))
    tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)
# Part 2: read messages
read_title_row = start_row_messages + len(unread_messages) + 1
tk.Label(main_frame, text="Read", font=("Arial", 12, "bold"), width=30).grid(row=read_title_row, column=col_incoming_message, padx=5, pady=5)
for i, sender in enumerate(read_messages): 
    i = i + read_title_row
    msg_formatted = sender + ": " + read_messages[sender]
    btn = tk.Button(main_frame, text="Delete")
    btn.grid(row=i+1, column=col_incoming_delete)
    btn.config(command=lambda widget=btn: clicked_delete_msg(widget, cols))
    tk.Label(main_frame, text=msg_formatted, width=20, relief=tk.SUNKEN).grid(row=i+1, column=col_incoming_message, padx=5, pady=5)


# Customize "Send Messages" Column
# Create one draft by default
num_drafts = create_new_draft(num_drafts)


# Start Up Main GUI
gui.mainloop()

