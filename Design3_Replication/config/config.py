# NOTES:
# all servers share same host
# each server has unique port = base port + pid
# PID automatically increments when you start new server on new terminal
# need to reset PID to 1 if you want to manually start over

# HOST        = "10.250.184.185"
HOST        = "127.0.0.1"       
BASE_PORT   = 12300             
PID         = 0  # 0 for leader, 1 and 2 for replicas
BUF_SIZE    = 4096

# Addresses of leader (0) and replicas (1,2)
REPLICA_ADDRESSES = {
    0: f"{HOST}:{BASE_PORT + 0}",
    1: f"{HOST}:{BASE_PORT + 1}",
    2: f"{HOST}:{BASE_PORT + 2}"
}

# Heartbeat settings (in seconds)
HEARTBEAT_INTERVAL = 5   # How often to send heartbeat messages
HEARTBEAT_TIMEOUT  = 10  # How long to wait before declaring a peer dead