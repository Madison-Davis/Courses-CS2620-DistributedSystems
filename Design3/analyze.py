import csv
import re
import sys

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

if __name__ == "__main__":
    # Use filename provided as command line argument or default to "log_file.txt"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "vm_logs/trial1/vm_0.log"
        
    try:
        logical_clocks, msg_queue_lengths = parse_file(filename)
        avg_jump, max_jump, avg_queue_length, max_queue_length = compute_stats(logical_clocks, msg_queue_lengths)
        
        print("Average Logical Clock Jump:", avg_jump)
        print("Maximum Logical Clock Jump:", max_jump)
        print("Average Message Queue Length:", avg_queue_length)
        print("Maximum Message Queue Length:", max_queue_length)
        
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
