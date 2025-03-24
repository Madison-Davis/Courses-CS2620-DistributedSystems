# config.py
import multiprocessing

# NOTES:
# each server must have a unique address = host:port

# HOST1     = "127.0.0.1"
HOST1       = "10.250.239.251"
HOST2       = "10.250.62.219"    
BASE_PORT   = 12300            
BUF_SIZE    = 4096

# HEARTBEAT_INTERVAL: How often to send heartbeat messages
# HEARTBEAT_TIMEOUT: How long to wait before declaring a peer dead
# PLOCK: Allows different objects to use the same lock
HEARTBEAT_INTERVAL = 2              
HEARTBEAT_TIMEOUT  = 10            
PLOCK = multiprocessing.Lock()      

# This is how we will start our databases
# Two servers on one and one server on another
# Leader starts as address 0
STARTING_ADDRESSES = {
    0: f"{HOST1}:{BASE_PORT + 0}",
    1: f"{HOST1}:{BASE_PORT + 1}",
    2: f"{HOST2}:{BASE_PORT + 2}"
}