import threading
import time

# Import our modules
import sql_connector
import receiving
import sending
import mock_server

def main():
    # Start mock agent servers for testing
    mock_server.start_mock_servers()
    
    # Connect to the database
    conn = sql_connector.connect_to_database()
    
    # Start producer and consumer threads
    producer = threading.Thread(
        target=receiving.producer_thread, 
        args=(conn, sql_connector),
        daemon=True,
        name="Producer"
    )
    consumer = threading.Thread(
        target=sending.consumer_thread, 
        args=(conn, sql_connector),
        daemon=True,
        name="Consumer"
    )
    
    print("Starting producer and consumer threads...")
    producer.start()
    consumer.start()
    
    # Return the database connection for use in the streamlit app
    return conn