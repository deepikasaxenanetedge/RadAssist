import mysql.connector
from receiving import add_log

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': '',  # Replace with your MySQL password
    'database': 'agent_flow',
    'port': '3307'
}

def connect_to_database():
    """Connect to the MySQL database and return the connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        add_log("Database Connection", f"Successfully connected to database: {DB_CONFIG['database']}")
        return conn
    except mysql.connector.Error as err:
        add_log("Database Error", f"Error connecting to database: {err}")
        exit(1)

def get_tag_ids(conn, tag_names):
    """Get tag IDs from tag names."""
    cursor = conn.cursor()
    tag_ids = []
    
    for tag_name in tag_names:
        query = "SELECT tag_id FROM tag_info WHERE tag_name = %s"
        cursor.execute(query, (tag_name,))
        result = cursor.fetchone()
        if result:
            tag_ids.append(result[0])
            add_log("Tag Lookup", f"Found tag ID {result[0]} for tag '{tag_name}'")
        else:
            add_log("Warning", f"Tag '{tag_name}' not found in database")
    
    cursor.close()
    return tag_ids

def get_agents_for_tag(conn, tag_id):
    """Get agent IDs assigned to a specific tag."""
    cursor = conn.cursor()
    query = "SELECT agent_id FROM agent_tags WHERE tag_id = %s"
    cursor.execute(query, (tag_id,))
    agents = cursor.fetchall()
    cursor.close()
    
    agent_ids = [agent[0] for agent in agents]
    add_log("Agent Lookup", f"Found {len(agents)} agents for tag {tag_id}: {agent_ids}")
    return agents

def get_agent_port(conn, agent_id):
    """Get port number for a specific agent."""
    cursor = conn.cursor()
    query = "SELECT port_number FROM agent_info WHERE agent_id = %s"
    cursor.execute(query, (agent_id,))
    port = cursor.fetchone()[0]
    cursor.close()
    
    add_log("Port Lookup", f"Agent {agent_id} is using port {port}")
    return port