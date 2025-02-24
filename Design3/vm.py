# virtual_machine.py



# +++++++++++++++ Imports/Installs +++++++++++++++ #
import os
import time
import config
import socket
import random
import config
import multiprocessing



# ++++++++++++++++++++ Class ++++++++++++++++++++ #

class VirtualMachine(multiprocessing.Process):
    def __init__(self, id):
        """ 
        Initialize Virtual Machine. 
        id              id of this vm (0, 1, 2, etc.)
        port            port of this vm (config.PORT + id, just to be more formal)
        peer_ports      all other vm ports, not including this vm
        queue           queue for incoming messages from other vms
        clock_speed     specify # of instructions per second for this vm
        logical_clock  
        log_file        specify where all log output should go for this vm 
        """
        super().__init__()
        # Create id, ports, and queue
        self.id = id
        self.port = config.PORT + id
        self.peer_ports = [(i, config.PORT + i) for i in range(config.NUM_VIRTUAL_MACHINES) if i != id]
        self.queue = multiprocessing.Queue()
        # Create clock
        self.clock_speed = random.randint(1, 6) # randomize number of instructions/second
        self.logical_clock = 0
        # Create and clear log file
        self.log_file = f"{config.LOG_DIR}vm_{id}.log"
        os.makedirs(config.LOG_DIR, exist_ok=True)
        open(self.log_file, 'w').close()

    def send_msg(self, recipient_vm_port, msg):
        """ Send a message to recipient vm's port. """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(("localhost", recipient_vm_port))
                msg = f"{self.id},{self.logical_clock}"
                s.sendall(msg.encode("utf-8"))
                return True
            except ConnectionRefusedError:
                return False
            
    def update(self, log_msg, sender_logical_clock=None):
        """ Update using logical clock rules and log a message. """
        # Logical clock rules
        if sender_logical_clock is not None:
            self.logical_clock = max(self.logical_clock, sender_logical_clock) + 1
        else:
            self.logical_clock += 1
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")
    
    def send_msg_and_update(self, list_of_recipients):
        """ Perform both sending a msg and updating for a list of recipient vms. """
        for recipient in list_of_recipients:
            # Create message (local logical clock time) and send it to the recipient's port
            recipient_vm_port = recipient[1]
            message = f"{self.id},{self.logical_clock}"
            status = self.send_msg(recipient_vm_port, message)
            # Update personal logical clock
            log_success = f"[Sent Msg To {recipient[0]}, System Time {time.time()}, Logical Clock Time {self.logical_clock}] SUCCESS"
            log_failure = f"[Sent Msg To {recipient[0]}, System Time {time.time()}, Logical Clock Time {self.logical_clock}] FAILURE"
            self.update(log_success) if status else self.update(log_failure)   

    def receive_msg(self):
        """ Listen for incoming/received messages and store them in a queue. """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", self.port))
            s.listen()
            while True:
                conn, _ = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        sender_id, sender_logical_clock = map(int, data.decode("utf-8").split(","))
                        # Put tuple (sender_id, sender_logical_clock) in a queue
                        self.queue.put((sender_id, sender_logical_clock))

    def handle_queue(self):
        """ Take one message off queue, update local logical clock, and write to log. """
        # Take one message off queue
        # Timeout=1 in case queue becomes empty
        # As an added, safeguard we also check before even calling handle_queue()
        sender_id, sender_logical_clock = self.queue.get(timeout=1) 
        # Update logical clock and write to log
        log_msg = f"[Received Msg From {sender_id}, System Time {time.time()}, New Msg Queue Length {self.queue.qsize()}, Logical Clock Time {self.logical_clock}]"
        self.update(log_msg, sender_logical_clock)

    def run(self):
        """ Main execution loop. """
        # Run a concurrent server socket to handle receive_msg()
        receiver_process = multiprocessing.Process(target=self.receive_msg, daemon=True)
        receiver_process.start()  

        try:
            while True:
                # Simulate clock speed (every 1/# th of a second, perform an instruction)
                time.sleep(1 / self.clock_speed)

                # If queue is not empty, perform the actions required
                if not self.queue.empty():
                    self.handle_queue()
                # If queue is empty, generate a random value
                else:
                    value = random.randint(1, 10)
                    # Send message to one machine
                    if value == 1:
                        self.send_msg_and_update([self.peer_ports[0]])
                    # Send message to other machines
                    elif value == 2:
                        self.send_msg_and_update([self.peer_ports[1]])
                    # Send message to both machines
                    elif value == 3:
                        self.send_msg_and_update(self.peer_ports)
                    # Internal event: simply increment logical clock and log info
                    else:
                        log_msg = f"[Internal, System Time {time.time()}, Logical Clock Time {self.logical_clock}] success"
                        self.update(log_msg)

        # Graceful termination
        except KeyboardInterrupt:
            print(f"Shutting down VM {self.id}...")
