# main.py



# +++++++++++++++ Imports/Installs +++++++++++++++ #
import config
from vm import VirtualMachine



# +++++++++++++++ Main Function +++++++++++++++ #

if __name__ == "__main__":
    # Initialization Stage: create VMs as objects from the class 'VirtualMachine'
        # Within each object...
        # vm creates a list all other vm ports to connect to
        # create and open new log file
        # create logical clock
    # NOTE: feel free to insert manually the clock speeds here for validation; we did it random
    #vms = [VirtualMachine(0,1),VirtualMachine(1,5),VirtualMachine(2,4)]
    vms = [VirtualMachine(i) for i in range(config.NUM_VIRTUAL_MACHINES)]

    # Print clock speed for knowledge-purposes
    for vm in vms:  
        print(f"vm {vm.id} created with clock speed {vm.clock_speed}")

    # Specify .start() to start up the VM as a process
    for vm in vms:
        vm.start() 
    # Specify .join() to keep the process alive
    for vm in vms:
        vm.join() 
