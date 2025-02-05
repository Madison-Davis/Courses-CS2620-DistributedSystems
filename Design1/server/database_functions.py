# +++++++++++++++  Imports/Installs  +++++++++++++++ #
import pandas as pd
import os


# ++++++++++++++++  Setup/Variables  ++++++++++++++++++ #

db_file = os.path.join(os.path.dirname(__file__), "database.csv")


# +++++++++++++++++  Functions  +++++++++++++++++ #

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
    """ Find the specified user and return their data. """
    df = pd.read_csv(db_file)
    return df.loc[df.iloc[:, 0] == user]

def db_get_all_users():
    """ Get all current users and return them as a list. """
    df = pd.read_csv(db_file)
    return df.iloc[:, 0].tolist()

def db_delete_user(user=None):
    """ Delete the user
    If user does not exist, then do nothing. 
    We take as true that each user's ID is unique in csv. """
    df = pd.read_csv(db_file)
    df.drop(df[df["username"] == user].index, inplace=True)


