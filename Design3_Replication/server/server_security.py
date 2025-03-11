# server_security.py



# +++++++++++++++ Imports/Installs +++++++++++++++ #
import os
import hashlib



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