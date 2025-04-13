from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status

from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessageResponse
from app.models.cassandra_models import MessageModel

class MessageController:
    """
    Controller for handling message operations
    """
    
    async def send_message(self, message_data: MessageCreate) -> MessageResponse:
        """
        Send a message from one user to another
        
        Args:
            message_data: The message data including content, sender_id, and receiver_id
            
        Returns:
            The created message with metadata
        
        Raises:
            HTTPException: If message sending fails
        """
        try:
            sender_id = int(message_data.sender_id)
            receiver_id = int(message_data.receiver_id)
            
            message = await MessageModel.create_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=message_data.content
            )
            
            return MessageResponse(
                message_id=message["message_id"],  
                sender_id=message["sender_id"],
                receiver_id=message["receiver_id"],
                conversation_id=message["conversation_id"],
                content=message["content"],
                timestamp=message["timestamp"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {str(e)}"
            )
    
    async def get_conversation_messages(
        self, 
        conversation_id: int, 
        page: int = 1, 
        limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get all messages in a conversation with pagination
        
        Args:
            conversation_id: ID of the conversation
            page: Page number
            limit: Number of messages per page
            
        Returns:
            Paginated list of messages
            
        Raises:
            HTTPException: If conversation not found or access denied
        """
        try:
            conversation_id = int(conversation_id)
            
            offset = (page - 1) * limit
            
            # Get messages
            messages = await MessageModel.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                offset=offset
            )
            
            has_more = len(messages) == limit
            
            message_responses = [
                MessageResponse(
                    message_id=msg["message_id"],  
                    sender_id=msg["sender_id"],
                    receiver_id=msg["receiver_id"],
                    conversation_id=msg["conversation_id"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                )
                for msg in messages
            ]
            
            return PaginatedMessageResponse(
                messages=message_responses,
                has_more=has_more
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get messages: {str(e)}"
            )
    
    async def get_messages_before_timestamp(
        self, 
        conversation_id: int, 
        before_timestamp: datetime,
        page: int = 1,
        limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get messages in a conversation before a specific timestamp with pagination
        
        Args:
            conversation_id: ID of the conversation
            before_timestamp: Get messages before this timestamp
            limit: Number of messages per page
            
        Returns:
            Paginated list of messages
            
        Raises:
            HTTPException: If conversation not found or access denied
        """
        try:
            conversation_id = int(conversation_id)
            
            messages = await MessageModel.get_messages_before_timestamp(
                conversation_id=conversation_id,
                before_timestamp=before_timestamp,
                limit=limit
            )
            
            has_more = len(messages) == limit
            
            message_responses = [
                MessageResponse(
                    message_id=msg["message_id"], 
                    sender_id=msg["sender_id"],
                    receiver_id=msg["receiver_id"],
                    conversation_id=msg["conversation_id"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                )
                for msg in messages
            ]
            
            return PaginatedMessageResponse(
                messages=message_responses,
                has_more=has_more
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get messages: {str(e)}"
            )