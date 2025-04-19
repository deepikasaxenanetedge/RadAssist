import json
import socket
import threading
import time
import datetime

# Access the global instant_solution and lock from receiving.py
from receiving import instant_solution, solution_lock, add_log

# Dict to store agent message history
agent_message_history = {}

def send_data_to_agent(port, data, tag_id, agent_id):
    """Send data to an agent at the specified port."""
    try:
        # Create a socket connection to the agent
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', port))
        
        # Send the data
        message = json.dumps({"data": data, "tag_id": tag_id})
        client_socket.send(message.encode('utf-8'))
        
        # Close the connection
        client_socket.close()
        
        # Log the send operation
        add_log("Message Sent", f"Sent data to agent {agent_id} at port {port}")
        
        # Store in agent history
        if port not in agent_message_history:
            agent_message_history[port] = []
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        agent_message_history[port].append({
            "time": timestamp,
            "data": data,
            "tag_id": tag_id
        })
        
        # Keep only the last 20 messages per agent
        if len(agent_message_history[port]) > 20:
            agent_message_history[port].pop(0)
        
        return True
    except Exception as e:
        add_log("Error", f"Error sending data to agent at port {port}: {e}")
        return False

def process_instant_solution(conn, sql_connector):
    """Process the instant solution and forward data to appropriate agents."""
    global instant_solution
    processed_item = False
    current_item = None
    tag_id = None
    tag_name = None
    data = None

    # Acquire lock before checking and modifying instant_solution
    with solution_lock:
        # Check if there's anything to process
        if not instant_solution:
            return False
        
        print(f"Debug - Processing Instant Solution: {instant_solution}")
        
        # Get the first tag's data to process
        current_item = instant_solution[0]
        tag_id = current_item[0]
        
        # Get the current message count for this tag
        msg_count = current_item[1]
        
        if msg_count > 0 and len(current_item) > 2:
            # Store the data to process after releasing the lock
            data_json = current_item[2]
            
            # Get tag name for logging
            cursor = conn.cursor()
            cursor.execute("SELECT tag_name FROM tag_info WHERE tag_id = %s", (tag_id,))
            tag_name_result = cursor.fetchone()
            tag_name = tag_name_result[0] if tag_name_result else f"Unknown Tag {tag_id}"
            cursor.close()
            
            add_log("Processing Tag", f"Processing tag '{tag_name}' (ID: {tag_id})")
            
            try:
                data = json.loads(data_json)["data"]
                
                # Decrement the message count
                current_item[1] -= 1
                
                # Remove the processed data entry
                current_item.pop(2)
                
                # Check if we should remove the tag entry
                if current_item[1] == 0 or len(current_item) <= 2:
                    instant_solution.pop(0)
                    
                processed_item = True
            except json.JSONDecodeError as e:
                add_log("Error", f"Failed to parse data JSON: {e}")
                # Remove problematic entry to avoid getting stuck
                current_item.pop(2)
                if current_item[1] > 0:
                    current_item[1] -= 1
                if current_item[1] == 0:
                    instant_solution.pop(0)
                return False
            except Exception as e:
                add_log("Error", f"Error processing instant solution item: {e}")
                return False
    
    if not processed_item or not tag_id or not data:
        return False
        
    # Get agents assigned to this tag (outside the lock)
    agents = sql_connector.get_agents_for_tag(conn, tag_id)
    
    if agents:
        add_log("Agents Found", f"Found {len(agents)} agents for tag {tag_id} ({tag_name})")
        
        # Send data to each agent (outside the lock)
        for agent in agents:
            agent_id = agent[0]
            port = sql_connector.get_agent_port(conn, agent_id)
            
            # Get agent name for logging
            cursor = conn.cursor()
            cursor.execute("SELECT agent_name FROM agent_info WHERE agent_id = %s", (agent_id,))
            agent_name_result = cursor.fetchone()
            agent_name = agent_name_result[0] if agent_name_result else f"Agent {agent_id}"
            cursor.close()
            
            add_log("Routing", f"Routing message to agent '{agent_name}' (ID: {agent_id}) on port {port}")
            send_data_to_agent(port, data, tag_id, agent_id)
    else:
        add_log("Warning", f"No agents found for tag {tag_id} ({tag_name})")
    
    return True

def consumer_thread(conn, sql_connector):
    """Consumer thread that processes the instant_solution and sends data to agents."""
    while True:
        try:
            # Only try to process if there's data
            process_instant_solution(conn, sql_connector)
            # Small sleep to prevent tight loop
            time.sleep(0.1)
        except Exception as e:
            add_log("Error", f"Error in consumer thread: {e}")
            time.sleep(1)

def get_agent_history():
    """Return the current history of messages sent to agents."""
    return agent_message_history