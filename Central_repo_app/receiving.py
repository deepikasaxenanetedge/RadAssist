import json
import re
import threading
import time
import datetime
from queue import Queue

# Shared data structure (instant_solution) and queue for producer-consumer pattern
instant_solution = []
message_queue = Queue()

# Create a lock for synchronizing access to instant_solution
solution_lock = threading.Lock()

# List to store processing logs
processing_logs = []

def add_log(title, description):
    """Add a log entry with timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "time": timestamp,
        "title": title,
        "description": description
    }
    processing_logs.append(log_entry)
    
    # Keep only the last 100 logs
    if len(processing_logs) > 100:
        processing_logs.pop(0)
    
    print(f"[{timestamp}] {title}: {description}")
    return log_entry

def dissemble_message(message):
    """Parse the input message to extract tags and data."""
    log_entry = add_log("Parsing Message", "Extracting tags and data from the message")
    
    # Extract tags and data using regex
    tags_pattern = r'<tags>\s*"tag"\s*:\s*"([^"]*)"?\s*</tags>'
    data_pattern = r'<data>\s*"data"\s*:\s*({[^}]+})\s*</data>'
    
    tags_match = re.search(tags_pattern, message)
    data_match = re.search(data_pattern, message)
    
    if not tags_match or not data_match:
        add_log("Error", "Invalid message format")
        return None
    
    # Extract tags
    tags_str = tags_match.group(1)
    tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else []
    
    # Extract data
    data_str = data_match.group(1)
    # Convert data string to proper JSON format
    data_str = data_str.replace("'", '"')
    try:
        data_dict = json.loads(data_str)
    except json.JSONDecodeError:
        # Handle case where data might be formatted differently
        data_dict = {"raw": data_str}
    
    result = {
        "tags": tags,
        "data": data_dict
    }
    
    add_log("Message Parsed", f"Tags: {', '.join(tags) if tags else 'None'}, Data: {json.dumps(data_dict)[:30]}...")
    return result

def update_instant_solution(tag_ids, data):
    """Update the instant solution 2D array with new data."""
    global instant_solution
    
    # Convert data to JSON string for storage
    data_json = json.dumps({"data": data})
    
    # Acquire lock before modifying instant_solution
    with solution_lock:
        for tag_id in tag_ids:
            # Check if tag_id already exists in instant_solution
            found = False
            for item in instant_solution:
                if item[0] == tag_id:
                    # Increment message count
                    item[1] += 1
                    # Add new data
                    item.append(data_json)
                    found = True
                    break
            
            # If tag_id not found, add new entry
            if not found:
                instant_solution.append([tag_id, 1, data_json])
        
        # Log the update
        solution_copy = [[item[0], item[1], len(item)-2] for item in instant_solution]
        add_log("Instant Solution Updated", f"Current state: {solution_copy}")
        print(f"Debug - Instant Solution: {instant_solution}")

# In receiving.py, update the producer_thread function:
def producer_thread(conn, sql_connector):
    """Producer thread that processes incoming messages and updates instant_solution."""
    while True:
        try:
            if not message_queue.empty():
                message = message_queue.get()
                add_log("Message Received", f"New message pulled from queue. Queue size: {message_queue.qsize()}")
                print(f"DEBUG - Processing message: {message[:100]}...")  # Log first 100 chars
                
                # Dissemble the message
                parsed_data = dissemble_message(message)
                if not parsed_data:
                    add_log("Error", "Failed to parse message")
                    message_queue.task_done()
                    continue
                
                # Get tag IDs
                tag_ids = sql_connector.get_tag_ids(conn, parsed_data["tags"])
                if not tag_ids:
                    add_log("Warning", f"No valid tags found in message. Tags: {parsed_data['tags']}")
                    message_queue.task_done()
                    continue
                
                # Update instant solution
                update_instant_solution(tag_ids, parsed_data["data"])
                add_log("Message Processed", f"Successfully added message to instant solution. Tag IDs: {tag_ids}")
                message_queue.task_done()
            else:
                time.sleep(0.1)
        except Exception as e:
            add_log("Error", f"Error in producer thread: {str(e)}")
            time.sleep(1)

def get_processing_logs():
    """Return the current list of processing logs."""
    return processing_logs