import streamlit as st
import time
import json
import datetime
import threading
from main import main
import receiving
import sending
import mock_server
import sql_connector

# Set page config
st.set_page_config(
    page_title="Agent Flow System",
    page_icon="🔄",
    layout="wide"
)

# Initialize session state
if 'messages_processed' not in st.session_state:
    st.session_state.messages_processed = 0
if 'last_message' not in st.session_state:
    st.session_state.last_message = None
if 'message_history' not in st.session_state:
    st.session_state.message_history = []
if 'logs_initialized' not in st.session_state:
    st.session_state.logs_initialized = False
if 'conn' not in st.session_state:
    # Initialize the system
    st.session_state.conn = main()

# Custom CSS for better visualization
st.markdown("""
    <style>
    .message-box {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .tag {
        display: inline-block;
        background-color: #e0f7fa;
        padding: 2px 8px;
        border-radius: 10px;
        margin: 2px;
        font-size: 0.8em;
    }
    .agent-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        background-color: #f5f5f5;
    }
    .data-flow {
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin: 5px 0;
    }
    .step-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        background-color: #f9f9f9;
    }
    .log-info {
        border-left: 3px solid #2196F3;
        padding-left: 10px;
    }
    .log-warning {
        border-left: 3px solid #FF9800;
        padding-left: 10px;
    }
    .log-error {
        border-left: 3px solid #F44336;
        padding-left: 10px;
    }
    .history-message {
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def format_message_display(message):
    """Format the message for better display"""
    return f"""```xml
{message}
```"""

def get_agent_info():
    """Get all agent information from the database"""
    conn = st.session_state.conn
    cursor = conn.cursor()
    
    # Get all agents
    cursor.execute("SELECT agent_id, agent_name, port_number FROM agent_info")
    agents = cursor.fetchall()
    
    # Get tag info for each agent
    agent_info = []
    for agent in agents:
        agent_id, agent_name, port = agent
        
        # Get tags for this agent
        cursor.execute("""
            SELECT t.tag_id, t.tag_name
            FROM tag_info t
            JOIN agent_tags at ON t.tag_id = at.tag_id
            WHERE at.agent_id = %s
        """, (agent_id,))
        tags = cursor.fetchall()
        
        # Get received messages
        received_messages = mock_server.get_received_messages().get(port, [])
        
        agent_info.append({
            "id": agent_id,
            "name": agent_name,
            "port": port,
            "tags": tags,
            "messages": received_messages
        })
    
    cursor.close()
    return agent_info

# App title
st.title("Agent Flow System Dashboard")
st.markdown("Visualize how messages are processed through the system")

# Create columns
col1, col2 = st.columns([1, 2])

with col1:
    # Message input form
    with st.form("message_form"):
        st.subheader("Send New Message")
        # In streamlit_app.py, update the default message input:
        message_input = st.text_area("Enter Message (XML format)", """<message>
            <tags>
                "tag": "test"
            </tags>
            <data>
                "data": {"test": "This is a test message"}
            </data>
        </message>""", height=200)
        
        submit_button = st.form_submit_button("Process Message")
        
        if submit_button:
            # Add to queue
            receiving.message_queue.put(message_input)
            st.session_state.last_message = message_input
            st.session_state.messages_processed += 1
            
            # Add message to history
            st.session_state.message_history.append({
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "message": message_input
            })
            
            # Keep only last 20 messages
            if len(st.session_state.message_history) > 20:
                st.session_state.message_history.pop(0)
            
            # Add log
            receiving.add_log("Message Submitted", "New message added to processing queue")
            
            st.success("Message added to processing queue!")
            
            # Show the message
            with st.expander("View Your Message"):
                st.markdown(format_message_display(message_input))
    
    # Message history
    with st.expander("Message History", expanded=False):
        if st.session_state.message_history:
            for idx, msg in enumerate(reversed(st.session_state.message_history)):
                st.markdown(f"**Message {idx+1} - {msg['time']}**")
                st.markdown(format_message_display(msg['message']))
                st.markdown("---")
        else:
            st.info("No message history yet")

with col2:
    # System visualization
    st.subheader("System Activity")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Processing Logs", "Instant Solution", "Agent Activity", "System Overview"])
    
    with tab1:
        logs_placeholder = st.empty()
    
    with tab2:
        solution_placeholder = st.empty()
    
    with tab3:
        agents_placeholder = st.empty()
        
    with tab4:
        # System overview with diagrams
        st.subheader("System Architecture")
        st.markdown("""
        This system processes messages with tags and routes them to appropriate agents:
        
        1. **Producer** - Parses messages and updates the instant solution
        2. **Instant Solution** - Stores tagged data waiting to be processed
        3. **Consumer** - Routes data to appropriate agents based on tags
        4. **Agents** - Receive data for processing (mock servers)
        """)
        
        # Database info
        st.subheader("Database Structure")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Tag Information**")
            conn = st.session_state.conn
            cursor = conn.cursor()
            cursor.execute("SELECT tag_id, tag_name FROM tag_info")
            tags = cursor.fetchall()
            
            tag_data = {"Tag ID": [], "Tag Name": []}
            for tag_id, tag_name in tags:
                tag_data["Tag ID"].append(tag_id)
                tag_data["Tag Name"].append(tag_name)
            
            st.dataframe(tag_data)
        
        with col2:
            st.markdown("**Agent Information**")
            cursor.execute("SELECT agent_id, agent_name, port_number FROM agent_info")
            agents = cursor.fetchall()
            
            agent_data = {"Agent ID": [], "Agent Name": [], "Port": []}
            for agent_id, agent_name, port in agents:
                agent_data["Agent ID"].append(agent_id)
                agent_data["Agent Name"].append(agent_name)
                agent_data["Port"].append(port)
            
            st.dataframe(agent_data)
            
            cursor.close()
    
    # Status bar
    status_placeholder = st.empty()

# Function to update UI in a separate thread to avoid blocking
def update_ui():
    # Update status bar
    with status_placeholder.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Messages in Queue", receiving.message_queue.qsize())
        with col2:
            st.metric("Messages Processed", st.session_state.messages_processed)
        with col3:
            st.metric("Active Tags in Solution", len(receiving.instant_solution))
    
    # Update logs
    with logs_placeholder.container():
        st.subheader("Processing Logs")
        logs = receiving.get_processing_logs()
        if logs:
            for log in reversed(logs):
                log_type = "info"
                if "Error" in log["title"]:
                    log_type = "error"
                elif "Warning" in log["title"]:
                    log_type = "warning"
                
                st.markdown(f"""
                <div class="step-card log-{log_type}">
                    <small>{log['time']}</small>
                    <p><strong>{log['title']}</strong></p>
                    <p>{log['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No processing logs yet")
    
    # Update instant solution
    # In streamlit_app.py, update the instant solution section:
    with solution_placeholder.container():
        st.subheader("Instant Solution State")
        try:
            with receiving.solution_lock:  # Acquire lock before accessing
                if receiving.instant_solution:
                    st.write(f"Number of tags in solution: {len(receiving.instant_solution)}")
                    for item in receiving.instant_solution:
                        if len(item) >= 2:  # Ensure item has at least tag_id and count
                            # Get tag name
                            conn = st.session_state.conn
                            cursor = conn.cursor()
                            cursor.execute("SELECT tag_name FROM tag_info WHERE tag_id = %s", (item[0],))
                            tag_result = cursor.fetchone()
                            tag_name = tag_result[0] if tag_result else f"Unknown Tag {item[0]}"
                            cursor.close()
                            
                            with st.expander(f"Tag: {tag_name} (ID: {item[0]}, Messages: {item[1]})", expanded=True):
                                if len(item) > 2:
                                    st.write(f"Data entries: {len(item)-2}")
                                    for i in range(2, len(item)):
                                        data = item[i]
                                        try:
                                            data_dict = json.loads(data)
                                            st.json(data_dict)
                                        except json.JSONDecodeError:
                                            st.text(f"Raw data: {data}")
                                else:
                                    st.info("No data entries for this tag yet")
                else:
                    st.info("No data in instant solution")
        except Exception as e:
            st.error(f"Error displaying instant solution: {str(e)}")

    
    # Update agents
    with agents_placeholder.container():
        st.subheader("Agent Activity")
        agent_info = get_agent_info()
        
        for agent in agent_info:
            with st.expander(f"{agent['name']} (Port: {agent['port']})"):
                # Display basic info
                st.markdown(f"**Agent ID:** {agent['id']}")
                
                # Display tags
                if agent['tags']:
                    st.markdown("**Tags:**")
                    tag_html = ""
                    for tag_id, tag_name in agent['tags']:
                        tag_html += f'<span class="tag">{tag_name}</span> '
                    st.markdown(tag_html, unsafe_allow_html=True)
                
                # Display messages
                st.markdown("**Message History:**")
                messages = sending.get_agent_history().get(agent['port'], [])
                
                if messages:
                    for idx, msg in enumerate(reversed(messages)):
                        st.markdown(f"**Message {idx+1} (Sent at {msg['time']}):**")
                        st.json(msg['data'])
                        
                        # Get tag name
                        cursor = st.session_state.conn.cursor()
                        cursor.execute("SELECT tag_name FROM tag_info WHERE tag_id = %s", (msg['tag_id'],))
                        tag_result = cursor.fetchone()
                        tag_name = tag_result[0] if tag_result else f"Unknown Tag {msg['tag_id']}"
                        cursor.close()
                        
                        st.markdown(f"For Tag: {tag_name} (ID: {msg['tag_id']})")
                        st.markdown("---")
                else:
                    st.info("No messages sent to this agent yet")

# Main app loop - keep refreshing the UI
placeholder = st.empty()
while True:
    update_ui()
    time.sleep(1)