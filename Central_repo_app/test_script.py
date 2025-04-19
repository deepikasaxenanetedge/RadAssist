import time
import receiving
import threading

# A script to send multiple test messages to the system

def send_test_messages():
    """Send multiple test messages to the system"""
    
    # Wait a moment for the system to initialize
    time.sleep(2)
    
    messages = [
        """<message>
    <tags>
        "tag": "Machine Learning,Data Processing"
    </tags>
    <data>
        "data": {'question': 'What is machine learning?'}
    </data>
</message>""",
        """<message>
    <tags>
        "tag": "Automation,Natural Language Processing"
    </tags>
    <data>
        "data": {'question': 'How can automation help with NLP?'}
    </data>
</message>""",
        """<message>
    <tags>
        "tag": "Computer Vision,API Development"
    </tags>
    <data>
        "data": {'question': 'What are good APIs for computer vision?'}
    </data>
</message>"""
    ]
    
    for i, message in enumerate(messages):
        print(f"Sending test message {i+1}")
        receiving.message_queue.put(message)
        time.sleep(3)  # Wait between messages
    
    print("All test messages sent")

if __name__ == "__main__":
    # Start in a separate thread so it doesn't block if run in main process
    test_thread = threading.Thread(target=send_test_messages)
    test_thread.daemon = True
    test_thread.start()