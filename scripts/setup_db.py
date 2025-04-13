"""
Script to initialize Cassandra keyspace and tables for the Messenger application.
"""
import os
import time
import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "messenger")

def wait_for_cassandra():
    """Wait for Cassandra to be ready before proceeding."""
    logger.info("Waiting for Cassandra to be ready...")
    cluster = None
    
    for i in range(20):  
        try:
            cluster = Cluster([CASSANDRA_HOST])
            session = cluster.connect()
            logger.info("Cassandra is ready!")
            return cluster
        except Exception as e:
            logger.warning(f"Cassandra not ready yet (attempt {i+1}/20): {str(e)}")
            time.sleep(5)  
    
    logger.error("Failed to connect to Cassandra after multiple attempts.")
    raise Exception("Could not connect to Cassandra")

def create_keyspace(session):
    """
    Create the keyspace if it doesn't exist.
    """
    logger.info(f"Creating keyspace {CASSANDRA_KEYSPACE} if it doesn't exist...")

    session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
    WITH REPLICATION = {{
        'class': 'SimpleStrategy',
        'replication_factor': 3
    }}
    """)

    logger.info(f"Keyspace {CASSANDRA_KEYSPACE} is ready.")

def create_tables(session):
    """
    Create the tables for the application based on our schema design.
    """
    logger.info("Creating tables...")

    session.execute("""
    CREATE TABLE IF NOT EXISTS messages_by_conversation (
        conversation_id bigint,
        created_at timestamp,
        message_id uuid,
        sender_id bigint,
        receiver_id bigint,
        content text,
        PRIMARY KEY (conversation_id, created_at, message_id)
    ) WITH CLUSTERING ORDER BY (created_at DESC, message_id DESC);
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS conversations_by_user (
        user_id bigint,
        last_message_at timestamp,
        conversation_id bigint,
        other_user_id bigint,
        last_message_content text,
        PRIMARY KEY (user_id, last_message_at, conversation_id)
    ) WITH CLUSTERING ORDER BY (last_message_at DESC, conversation_id DESC);
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS conversation_metadata (
        conversation_id bigint,
        user1_id bigint,
        user2_id bigint,
        created_at timestamp,
        last_message_at timestamp,
        last_message_content text,
        PRIMARY KEY (conversation_id)
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS user_conversations_lookup (
        user1_id bigint,
        user2_id bigint,
        conversation_id bigint,
        PRIMARY KEY ((user1_id, user2_id))
    );
    """)

    logger.info("Tables created successfully.")

def main():
    """Initialize the database."""
    logger.info("Starting Cassandra initialization...")

    cluster = wait_for_cassandra()

    try:
        session = cluster.connect()

        create_keyspace(session)
        session.set_keyspace(CASSANDRA_KEYSPACE)
        create_tables(session)

        logger.info("Cassandra initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise
    finally:
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    main()