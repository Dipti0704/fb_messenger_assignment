# FB Messenger Backend with Cassandra

This project implements a Facebook Messenger-style backend using Apache Cassandra as the distributed database. It provides APIs for messaging functionality built with FastAPI and uses Cassandra's distributed architecture to ensure high availability and scalability.

## Architecture Overview

The application follows a structured FastAPI architecture:

- `app/`: Main application package
  - `api/`: API routes and endpoints
    - `routes/`: Route handlers for conversations and messages
  - `controllers/`: Business logic for conversations and messages
  - `models/`: Database interaction with Cassandra
  - `schemas/`: Pydantic models for validation
  - `db/`: Database utilities including Cassandra client
- `scripts/`: Utility scripts for database setup and test data generation

## Data Model

The Cassandra data model is designed for efficient message handling with four main tables:

1. **messages_by_conversation**: Stores messages organized by conversation with timestamps
2. **conversations_by_user**: Tracks conversations per user with latest message data
3. **conversation_metadata**: Stores conversation details and metadata
4. **user_conversations_lookup**: Enables efficient lookups between users and conversations

### Schema Design Highlights

```sql
-- Messages organized by conversation
CREATE TABLE messages_by_conversation (
    conversation_id bigint,
    created_at timestamp,
    message_id uuid,
    sender_id bigint,
    receiver_id bigint,
    content text,
    PRIMARY KEY (conversation_id, created_at, message_id)
) WITH CLUSTERING ORDER BY (created_at DESC, message_id DESC);

-- User conversations with recent message info
CREATE TABLE conversations_by_user (
    user_id bigint,
    last_message_at timestamp,
    conversation_id bigint,
    other_user_id bigint,
    last_message_content text,
    PRIMARY KEY (user_id, last_message_at, conversation_id)
) WITH CLUSTERING ORDER BY (last_message_at DESC, conversation_id DESC);
```

The schema is optimized for:
- Fast retrieval of messages in a conversation
- Efficient lookup of a user's recent conversations
- Support for pagination in both conversations and messages
- Querying messages before a specific timestamp

## Features

- **User Conversations**: Retrieve all conversations for a user
- **Conversation Details**: Get specific conversation metadata
- **Message Sending**: Send messages between users
- **Message Retrieval**: Get messages in a conversation with pagination
- **Time-based Queries**: Retrieve messages before a specific timestamp

## API Endpoints

### Conversations

- `GET /api/conversations/user/{user_id}`: Get all conversations for a user
  - Parameters: 
    - `user_id`: ID of the user
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20)

- `GET /api/conversations/{conversation_id}`: Get a specific conversation
  - Parameters: 
    - `conversation_id`: ID of the conversation

### Messages

- `POST /api/messages/`: Send a message
  - Body: 
    ```json
    {
      "sender_id": 1,
      "receiver_id": 2,
      "content": "Hello there!"
    }
    ```

- `GET /api/messages/conversation/{conversation_id}`: Get messages in a conversation
  - Parameters:
    - `conversation_id`: ID of the conversation
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20)

- `GET /api/messages/conversation/{conversation_id}/before`: Get messages before timestamp
  - Parameters:
    - `conversation_id`: ID of the conversation
    - `before_timestamp`: ISO format timestamp
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20)

## Setup and Installation

### Quick Start with Docker

1. Clone this repository
2. Make sure Docker and Docker Compose are installed
3. Run the initialization script:
   ```bash
   ./init.sh
   ```

This will:
- Start the FastAPI application and Cassandra containers
- Initialize the Cassandra keyspace and tables
- Make the API available at http://localhost:8000

Access API documentation at http://localhost:8000/docs

To stop the application:
```bash
docker-compose down
```

### Manual Setup

If you prefer not to use Docker:

1. Install Cassandra locally and start it
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   python scripts/setup_db.py
   ```
5. Start the FastAPI application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Test Data

Generate test data for development:

```bash
docker-compose exec app python scripts/generate_test_data.py
```

This creates:
- 10 test users (IDs 1-10)
- 15 conversations between random pairs of users
- Multiple messages in each conversation

## Performance Considerations

The Cassandra data model is designed with these distributed system principles:

1. **Data Distribution**: Partition keys spread data evenly across the cluster
2. **Minimal Hotspots**: Conversation IDs as partition keys distribute load
3. **Write Efficiency**: Optimized for high-throughput message writing
4. **Read Patterns**: Tables designed for specific read patterns
5. **Pagination Support**: Efficient cursor-based pagination

## Cassandra Best Practices Implemented

- **Denormalization**: Data is duplicated across tables for read efficiency
- **Partition Key Selection**: Careful selection to avoid hotspots
- **Clustering Columns**: Used for sorting and efficient range queries
- **Secondary Indexes**: Avoided in favor of denormalization
- **Consistency Levels**: Configurable based on business requirements

