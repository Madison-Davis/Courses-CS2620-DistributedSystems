# config.py
import multiprocessing

# ALL_HOSTS: All globally known hosts upon startup
# MAX_PID: max_pid that client will try before stopping search
# For testing, simply set 'ALL_HOSTS' to 127.0.0.1
ALL_HOSTS    = ["127.0.0.1"]  #  "10.250.239.251", "10.250.62.219",
BASE_PORT   = 12300            
BUF_SIZE    = 4096
MAX_PID     = 1000

# HEARTBEAT_INTERVAL: How often to send heartbeat messages
# HEARTBEAT_TIMEOUT: How long to wait before declaring a peer dead
# PLOCK: Allows different objects to use the same lock
HEARTBEAT_INTERVAL = 2              
HEARTBEAT_TIMEOUT  = 10            
PLOCK = multiprocessing.Lock()      
