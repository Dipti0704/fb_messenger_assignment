"""
Cassandra models for the Messenger application.
"""

import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from app.db.cassandra_client import cassandra_client

class MessageModel:
    """
    Message model for interacting with the messages table.
    """
    
    @staticmethod
    async def create_message(
        sender_id: int, 
        receiver_id: int, 
        content: str, 
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new message in a conversation.
        
        If conversation_id is not provided, this method should look up or create
        a conversation between the sender and receiver.
        
        Args:
            sender_id: ID of the message sender
            receiver_id: ID of the message receiver
            content: Content of the message
            conversation_id: Optional ID of the conversation
            
        Returns:
            Dict containing the created message data
        """
        timestamp = datetime.utcnow()
        
        message_id = uuid.uuid4()
        
        sender_id = int(sender_id)
        receiver_id = int(receiver_id)
        
        if conversation_id is None:
            conversation_id = await ConversationModel.create_or_get_conversation(
                user1_id=sender_id,
                user2_id=receiver_id
            )
        
        conversation_id = int(conversation_id)
        
        query = """
            INSERT INTO messages_by_conversation (
                conversation_id, created_at, message_id, sender_id, receiver_id, content
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        cassandra_client.execute(query, (
            conversation_id, timestamp, message_id, sender_id, receiver_id, content
        ))
        
        update_query = """
            INSERT INTO conversations_by_user (
                user_id, last_message_at, conversation_id, other_user_id, last_message_content
            ) VALUES (%s, %s, %s, %s, %s)
        """
        cassandra_client.execute(update_query, (
            sender_id, timestamp, conversation_id, receiver_id, content
        ))
        cassandra_client.execute(update_query, (
            receiver_id, timestamp, conversation_id, sender_id, content
        ))
        
        metadata_query = """
            UPDATE conversation_metadata SET 
                last_message_at = %s, 
                last_message_content = %s
            WHERE conversation_id = %s
        """
        cassandra_client.execute(metadata_query, (
            timestamp, content, conversation_id
        ))
        
        return {
            "message_id": str(message_id),
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "timestamp": timestamp.isoformat()
        }

    @staticmethod
    async def get_conversation_messages(
        conversation_id: Union[int, str], 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation with pagination.
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        conversation_id = int(conversation_id)
        
        query = """
            SELECT * FROM messages_by_conversation
            WHERE conversation_id = %s
            LIMIT %s
        """
        rows = cassandra_client.execute(query, (conversation_id, limit + offset))
        
        messages = list(rows)[offset:] if offset > 0 else list(rows)
        
        return [
            {
                "message_id": str(row["message_id"]),
                "conversation_id": row["conversation_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "content": row["content"],
                "timestamp": row["created_at"].isoformat()
            }
            for row in messages
        ]
    
    @staticmethod
    async def get_messages_before_timestamp(
        conversation_id: Union[int, str], 
        before_timestamp: datetime, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get messages before a timestamp with pagination.
        
        Args:
            conversation_id: ID of the conversation
            before_timestamp: Get messages before this timestamp
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        conversation_id = int(conversation_id)
        
        query = """
            SELECT * FROM messages_by_conversation
            WHERE conversation_id = %s AND created_at < %s
            LIMIT %s
        """
        rows = cassandra_client.execute(query, (conversation_id, before_timestamp, limit))
        
        return [
            {
                "message_id": str(row["message_id"]),
                "conversation_id": row["conversation_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "content": row["content"],
                "timestamp": row["created_at"].isoformat()
            }
            for row in rows
        ]


class ConversationModel:
    """
    Conversation model for interacting with the conversations-related tables.
    """
    
    @staticmethod
    async def get_user_conversations(
        user_id: int, 
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Get conversations for a user with pagination.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of conversations to return
            
        Returns:
            Tuple of (conversations, has_more)
        """
        user_id = int(user_id)
        
        query = """
            SELECT * FROM conversations_by_user
            WHERE user_id = %s
            LIMIT %s
        """
        rows = cassandra_client.execute(query, (user_id, limit))
        
        conversations = [
            {
                "conversation_id": row["conversation_id"],
                "other_user_id": row["other_user_id"],
                "last_updated": row["last_message_at"].isoformat(),
                "last_message": row["last_message_content"]
            }
            for row in rows
        ]
        
        has_more = len(conversations) == limit
        
        return conversations, has_more
    
    @staticmethod
    async def get_conversation(
        conversation_id: Union[int, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation details dictionary
        """
        conversation_id = int(conversation_id)
        
        query = """
            SELECT * FROM conversation_metadata
            WHERE conversation_id = %s
        """
        rows = cassandra_client.execute(query, (conversation_id,))
        
        if not rows:
            return None
        
        row = rows[0]
        return {
            "conversation_id": row["conversation_id"],
            "participant_ids": [row["user1_id"], row["user2_id"]],
            "created_at": row["created_at"].isoformat(),
            "last_updated": row["last_message_at"].isoformat() if row["last_message_at"] else row["created_at"].isoformat()
        }
    
    @staticmethod
    async def create_or_get_conversation(
        user1_id: int, 
        user2_id: int
    ) -> int:
        """
        Get an existing conversation between two users or create a new one.
        
        This ensures we don't create duplicate conversations between the same users.
        
        Args:
            user1_id: ID of the first user
            user2_id: ID of the second user
            
        Returns:
            Conversation ID as integer
        """
        user1_id = int(user1_id)
        user2_id = int(user2_id)
        
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        lookup_query = """
            SELECT conversation_id FROM user_conversations_lookup
            WHERE user1_id = %s AND user2_id = %s
        """
        rows = cassandra_client.execute(lookup_query, (user1_id, user2_id))
        
        if rows:
            return rows[0]["conversation_id"]
        
        timestamp = datetime.utcnow()
      
        conversation_id = int(time.time() * 1000) + (user1_id * 1000) + (user2_id % 1000)
        
        insert_lookup = """
            INSERT INTO user_conversations_lookup (user1_id, user2_id, conversation_id)
            VALUES (%s, %s, %s)
        """
        cassandra_client.execute(insert_lookup, (user1_id, user2_id, conversation_id))
        
        insert_metadata = """
            INSERT INTO conversation_metadata (
                conversation_id, user1_id, user2_id, created_at, last_message_at
            ) VALUES (%s, %s, %s, %s, NULL)
        """
        cassandra_client.execute(insert_metadata, (
            conversation_id, user1_id, user2_id, timestamp
        ))
        
        return conversation_id