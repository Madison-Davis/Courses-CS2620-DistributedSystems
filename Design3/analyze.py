# analyze.py



# +++++++++++++++ Imports/Installs +++++++++++++++ #
import csv
import re
import sys



# +++++++++++++++ Helper Functions +++++++++++++++ #

def parse_file(filename):
    """
    Parses the tab-separated log file.
    Extracts all Logical Clock Time values and message queue lengths.
    """
    logical_clocks = []
    msg_queue_lengths = []
    
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            for field in row:
                # Look for the logical clock time field
                if "Logical Clock Time" in field:
                    match = re.search(r"Logical Clock Time\s+(\d+)", field)
                    if match:
                        logical_clock_val = int(match.group(1))
                        logical_clocks.append(logical_clock_val)
                # Look for the message queue length field
                if "New Msg Queue Length" in field:
                    match = re.search(r"New Msg Queue Length\s+(\d+)", field)
                    if match:
                        msg_queue_val = int(match.group(1))
                        msg_queue_lengths.append(msg_queue_val)
                        
    return logical_clocks, msg_queue_lengths

def compute_stats(logical_clocks, msg_queue_lengths):
    """
    Computes the differences (jumps) between consecutive logical clock values,
    then calculates the average and maximum jump. Also computes the average and
    maximum message queue lengths.
    """
    jumps = []
    for i in range(1, len(logical_clocks)):
        jump = logical_clocks[i] - logical_clocks[i - 1]
        jumps.append(jump)
        
    avg_jump = sum(jumps) / len(jumps) if jumps else 0
    max_jump = max(jumps) if jumps else 0
    
    avg_queue_length = sum(msg_queue_lengths) / len(msg_queue_lengths) if msg_queue_lengths else 0
    max_queue_length = max(msg_queue_lengths) if msg_queue_lengths else 0
    
    return avg_jump, max_jump, avg_queue_length, max_queue_length



# +++++++++++++++ Main Function +++++++++++++++ #

if __name__ == "__main__":
    # Use filename provided as command line argument or default to "log_file.txt"
    if len(sys.argv) > 1:
        filenames = [sys.argv[1]]
    else:
        # Define all the files to parse
        """
        Exp 1, Slowest
        filenames = [
            "vm_logs/trial1/vm_2.log",
            "vm_logs/trial2/vm_0.log",
            "vm_logs/trial3/vm_1.log",
            "vm_logs/trial4/vm_0.log",
            "vm_logs/trial5/vm_1.log",
            "vm_logs/trial6/vm_1.log",
            "vm_logs/trial7/vm_0.log",
            "vm_logs/trial8/vm_0.log",
            ]

        Exp 1, Fastest
        filenames = [
            "vm_logs/trial1/vm_0.log",
            "vm_logs/trial2/vm_2.log",
            "vm_logs/trial3/vm_0.log",
            "vm_logs/trial4/vm_2.log",
            "vm_logs/trial5/vm_0.log",
            "vm_logs/trial6/vm_0.log",
            "vm_logs/trial7/vm_1.log",
            "vm_logs/trial8/vm_1.log",
            ]

        Exp 2, Slowest
        filenames = [
            "vm_logs/speed_trial1/vm_0.log",
            "vm_logs/speed_trial2/vm_0.log",
            "vm_logs/speed_trial3/vm_2.log",
            "vm_logs/speed_trial4/vm_2.log",
            "vm_logs/speed_trial5/vm_2.log"
            ]

        Exp 2, Fastest
        filenames = [
            "vm_logs/speed_trial1/vm_1.log",
            "vm_logs/speed_trial2/vm_1.log",
            "vm_logs/speed_trial3/vm_0.log",
            "vm_logs/speed_trial4/vm_1.log",
            "vm_logs/speed_trial5/vm_0.log"
            ]

        Exp 3, Slowest
        filenames = [
            "vm_logs/internal_trial1/vm_2.log",
            "vm_logs/internal_trial2/vm_2.log",
            "vm_logs/internal_trial3/vm_1.log",
            "vm_logs/internal_trial4/vm_1.log",
            "vm_logs/internal_trial5/vm_1.log"
            ]

        Exp 2, Fastest
        filenames = [
            "vm_logs/internal_trial1/vm_1.log",
            "vm_logs/internal_trial2/vm_0.log",
            "vm_logs/internal_trial3/vm_2.log",
            "vm_logs/internal_trial4/vm_0.log",
            "vm_logs/internal_trial5/vm_2.log"
            ]

        Exp 4, Slowest
        filenames = [
            "vm_logs/speed_internal_trial1/vm_0.log",
            "vm_logs/speed_internal_trial2/vm_0.log",
            "vm_logs/speed_internal_trial3/vm_1.log",
            "vm_logs/speed_internal_trial4/vm_1.log",
            "vm_logs/speed_internal_trial5/vm_1.log"
            ]

        Exp 4, Fastest
        filenames = [
            "vm_logs/speed_internal_trial1/vm_1.log",
            "vm_logs/speed_internal_trial2/vm_1.log",
            "vm_logs/speed_internal_trial3/vm_2.log",
            "vm_logs/speed_internal_trial4/vm_0.log",
            "vm_logs/speed_internal_trial5/vm_0.log"
            ]
        """
        
        filenames = [
            "vm_logs/speed_internal_trial1/vm_1.log",
            "vm_logs/speed_internal_trial2/vm_1.log",
            "vm_logs/speed_internal_trial3/vm_2.log",
            "vm_logs/speed_internal_trial4/vm_0.log",
            "vm_logs/speed_internal_trial5/vm_0.log"
            ]
        
        # NOTE: queue lengths for experiment 1
        # Exp 1: (266-187)+(389-273)+(385-265)+(3)+(378-250)+(4)+(1)+(328-211)
        # NOTE: queue lengths for experiment 4
        # Exp 4: (213-128) + (209-206) + (215-148) + (214-135) + (213-178)
        
    try:
        total_avg_jump = 0
        total_max_jump = 0
        total_avg_queue = 0
        total_max_queue_length = 0
        num_files = len(filenames)

        for filename in filenames:
            logical_clocks, msg_queue_lengths = parse_file(filename)
            avg_jump, max_jump, avg_queue_length, max_queue_length = compute_stats(logical_clocks, msg_queue_lengths)
            
            total_avg_jump += avg_jump
            total_max_jump += max_jump
            total_avg_queue += avg_queue_length
            total_max_queue_length += max_queue_length

        print("Average Logical Clock Jump:", total_avg_jump/num_files)
        print("Maximum Logical Clock Jump:", total_max_jump/num_files)
        print("Average Message Queue Length:", total_avg_queue/num_files)
        print("Maximum Message Queue Length:", total_max_queue_length/num_files)
        
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
