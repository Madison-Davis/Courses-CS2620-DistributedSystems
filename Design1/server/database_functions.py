# +++++++++++++++  Imports/Installs  +++++++++++++++ #
import pandas as pd
import os


# ++++++++++++++++  Setup/Variables  ++++++++++++++++++ #

db_file = os.path.join(os.path.dirname(__file__), "database.csv")


# +++++++++++++++++  Functions  +++++++++++++++++ #

def db_read_file():
    """ Reads the database and returns None if nothing is in there. """
    if os.path.exists(db_file) and os.path.getsize(db_file) > 0:
        with open(db_file, 'r') as file:
            content = file.read().strip()
            if content:
                return pd.read_csv(db_file)
    return None

def db_create_new_user(user, pwd):
    """ Create a new user DataFrame from information and save to csv. 
    Assume because they have not been a user before, they have no messages/drafts. """
    frame = pd.DataFrame({
        "username": [user],
        "password": [pwd],
        "messages": [",".join([])],
        "drafts": [",".join(["d1"])],
    })
    frame.to_csv(db_file, mode='a', header=not os.path.exists(db_file), index=False)

def db_get_user_data(user=None):
    """ Find the specified user and return their data. 
    If the user does not exist in the database, return None. """
    df = db_read_file()
    if df is not None:
        user_data = df.loc[df.iloc[:, 0] == user]
        if user_data.empty == False:
            return user_data
    return None
        
def db_get_all_users(exclude_user=None):
    """ Get all current users and return them as a list."""
    # TODO: exclude current client's name
    df = pd.read_csv(db_file)
    if exclude_user is not None:
        df_filtered = df[df.iloc[:, 0] != exclude_user]
        return df_filtered.iloc[:, 0].tolist()
    return df.iloc[:, 0].tolist()

def db_delete_user(user=None):
    """ Delete the user
    If user does not exist, then do nothing. 
    We take as true that each user's ID is unique in csv. 
    Only way to delete a user is to login, so df will be non-empty. """
    df = pd.read_csv(db_file)
    df.drop(df[df["username"] == user].index, inplace=True)


