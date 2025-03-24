# config.py
import multiprocessing

# NOTES:
# all servers share same host
# each server has unique port = base port + pid
# PID automatically increments when you start new server on new terminal
# need to reset PID to 1 if you want to manually start over

# ALL_HOSTS: All known hosts, as a simple guide
# MAX_PID: max_pid that client will try before stopping
ALL_HOSTS    = ["10.250.239.251", "10.250.62.219", "127.0.0.1"] 
BASE_PORT   = 12300            
BUF_SIZE    = 4096
MAX_PID     = 1000

# HEARTBEAT_INTERVAL: How often to send heartbeat messages
# HEARTBEAT_TIMEOUT: How long to wait before declaring a peer dead
# PLOCK: Allows different objects to use the same lock
HEARTBEAT_INTERVAL = 2              
HEARTBEAT_TIMEOUT  = 10            
PLOCK = multiprocessing.Lock()      
