import socket
import threading
import time
import json

# Dict to store received messages
received_messages = {}

def mock_agent_server(port):
    """Create a mock agent server for testing."""
    global received_messages
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)
    print(f"Mock server listening on port {port}")
    
    while True:
        try:
            client_socket, _ = server_socket.accept()
            data = client_socket.recv(1024).decode('utf-8')
            print(f"Agent on port {port} received: {data}")
            
            # Store the latest message
            try:
                received_messages[port] = json.loads(data)
            except json.JSONDecodeError:
                received_messages[port] = {"raw": data}
                
            client_socket.close()
        except Exception as e:
            print(f"Error in mock server on port {port}: {e}")
            break

def start_mock_servers():
    """Start mock servers for testing."""
    ports = [5000, 5001, 5002, 5003, 5004, 5005]
    
    server_threads = []
    for port in ports:
        server_thread = threading.Thread(target=mock_agent_server, args=(port,))
        server_thread.daemon = True
        server_thread.start()
        server_threads.append(server_thread)
    
    # Give servers time to start
    time.sleep(1)
    
    return server_threads

def get_received_messages():
    """Return the current dict of received messages."""
    return received_messages