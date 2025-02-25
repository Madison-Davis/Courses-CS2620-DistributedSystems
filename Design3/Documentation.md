# CS 2620 Design Exercise 3: Scale Models

-------------------------------------------
## Design Requirements

This project requires us to build a small, asynchronous distributed system that runs on one single machine.


1. The system consists of multiple 'virtual machines' running at different speeds determined by logical clocks.
2. During initialization of each machine, pick a random number 1-6, and that will be the number of clock ticks per (real world) second for that machine.
3. Each machine will have a network queue that is not constrained to the n operations per second in which it will hold incoming messages.
4. The (virtual) machine should listen on one or more sockets for such messages.
5. Connect each of the vms to each other so messages can be passed between them during initialization, not constrained to happen at the speed of the internal model clocks.
6. Each virtual machine should open a file as a log.
7. Update each vm's logical clock using the rules for logical clocks.

After initialization, the following mechanism should be employed:
1. On each clock cycle, if there is a message in the message queue for the machine, the vm should take one message off the queue, update the local logical clock, and write in the log that it received a message, the global time (gotten from the system), the length of the message queue, and the logical clock time.
2. If there is no message in the queue, the virtual machine should generate a 'value', a random number in the range of 1-10.
3. If the value is 1, send to one of the other machines a message that is the local logical clock time, update it’s own logical clock, and update the log with the send, the system time, and the logical clock time
4. If the value is 2, send to the other virtual machine a message that is the local logical clock time, update it’s own logical clock, and update the log with the send, the system time, and the logical clock time.
5. If the value is 3, send to both of the other virtual machines a message that is the logical clock time, update it’s own logical clock, and update the log with the send, the system time, and the logical clock time.
6. If the value is other than 1-3, treat the cycle as an internal event; update the local logical clock, and log the internal event, the system time, and the logical clock value.


-------------------------------------------
## System Design Decisions

Based on the requirements, here is our system design:
1. Because vms will only be sending and receiving messages, it makes sense to just make one class of sending/receiving capability, then make objects of this class.
2. If this project runs on just one computer, then we decided to use processes to run concurrently.
3. For each process, we’ll assign it one vm, where the vm will pull up its own “server” thread to then handle lookups for any received messages.
4. For communicating, we employ a simple form of inter-process communication via sockets.
5. Let the data being sent over the sockets be serialized strings, such as “id,msg”.



-------------------------------------------
## Code: Setup

Clone the repository.
Navigte to `Design3`

Run :
`pyython3 main.py`



-------------------------------------------
## Code: Structure

```
├── vm.py          → a class for each vm we make, includes sending/receiving/updating capability
├── vm_logs/       → all the log files where each file is named vm_{id}.log
├── main.py        → starts the program: creates 3 vm objects on different processes and starts them up
└── config.py      → specifications like the port number, how many vms we want, and log file
```



-------------------------------------------
## Code: vm.py

vm.py offers a class 'VirtualMachine' where each object of the class can send messages, receive messages, and update internal variables.
Shown below are all of its functions (besides `__init__`):

```
Function               Parameters                                Description
send_msg               (recipient_vm_port (int), msg (string))   → send a message to the recipient’s vm port
update                 (sender_logical_clock (optional int))     → update the logical clock using logical clock rules 
log                    (msg (sring))                             → log a message to our vm’s log_file
send_msg_and_update    (list_of_recipients (int list))           → perform both send_msg, update, and log in one step for a list of recipients who we will send message(s) to
receive_msg                                                      → listen for incoming/received messages and store them in a queue
handle_queue                                                     → take one message off queue, update local logical clock, and write to log
run                                                              → main execution loop (when we start up the vm object in a process, this is what runs)
```

Here are all of its internal variables, defined in `__init__`:
```
id              → the id of this vm (0,1,2,etc.)
port            → the port of this vm (config.PORT + id)
peer_ports      → a list of all other vm ports, not including this one
queue           → a queue for incoming messages from other vms
clock_speed     → a random # from 1-6 that specifies # of instructions/second
logical_clock   → an updatable int to represent how far-along this vm is
log_file        → the specific vm’s log file made within vm_logs/
```


