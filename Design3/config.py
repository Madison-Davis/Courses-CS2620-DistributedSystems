# config.py

NUM_VIRTUAL_MACHINES = 3        # how many virtual machines are we going to simulate?
PORT = 12321                    # what port should the machines all connect to to communicate?
LOG_DIR = "vm_logs/internal_trial5/"     # directory for where the virtual machines' log files will go
SPEED_UPPER_BOUND = 6           # upper bound for random clock speed
INTERNAL_UPPER_BOUND = 5       # upper bound for random int generation in case of no message in queue - must be >=3, higher means higher probability of internal event