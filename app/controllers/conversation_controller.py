from fastapi import HTTPException, status
from typing import Union, Optional
import uuid

from app.schemas.conversation import ConversationResponse, PaginatedConversationResponse, ConversationListItem
from app.models.cassandra_models import ConversationModel

class ConversationController:
    """
    Controller for handling conversation operations
    """
    
    async def get_user_conversations(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 20
    ) -> PaginatedConversationResponse:
        """
        Get all conversations for a user with pagination
        
        Args:
            user_id: ID of the user
            page: Page number
            limit: Number of conversations per page
            
        Returns:
            Paginated list of conversations
            
        Raises:
            HTTPException: If user not found or access denied
        """
        try:
            # Ensure user_id is an integer
            user_id = int(user_id)
            
            # Get conversations for user
            conversations, has_more = await ConversationModel.get_user_conversations(
                user_id=user_id,
                limit=limit
            )
            
            # Convert to response format
            conversation_items = [
                ConversationListItem(
                    conversation_id=conv["conversation_id"],
                    other_user_id=conv["other_user_id"],
                    last_updated=conv["last_updated"],
                    last_message=conv["last_message"]
                )
                for conv in conversations
            ]
            
            return PaginatedConversationResponse(
                conversations=conversation_items,
                has_more=has_more
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get conversations: {str(e)}"
            )
    
    async def get_conversation(
        self, 
        conversation_id: Union[int, str]
    ) -> ConversationResponse:
        """
        Get a specific conversation by ID
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation details
            
        Raises:
            HTTPException: If conversation not found or access denied
        """
        try:
            # Ensure conversation_id is an integer
            conversation_id = int(conversation_id)
            
            # Get conversation by ID
            conversation = await ConversationModel.get_conversation(conversation_id=conversation_id)
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            return ConversationResponse(
                conversation_id=conversation["conversation_id"],
                participant_ids=conversation["participant_ids"],
                created_at=conversation["created_at"],
                last_updated=conversation["last_updated"]
            )
        except HTTPException:
            # Re-throw HTTP exceptions
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get conversation: {str(e)}"
            )
            
    async def create_or_get_conversation(
        self,
        user1_id: int,
        user2_id: int
    ) -> ConversationResponse:
        """
        Create a new conversation between two users or get an existing one
        
        Args:
            user1_id: ID of the first participant
            user2_id: ID of the second participant
            
        Returns:
            The created or retrieved conversation
            
        Raises:
            HTTPException: If conversation creation fails
        """
        try:
            # Ensure user IDs are integers
            user1_id = int(user1_id)
            user2_id = int(user2_id)
            
            # Create or get conversation
            conversation_id = await ConversationModel.create_or_get_conversation(
                user1_id=user1_id,
                user2_id=user2_id
            )
            
            # Get the conversation details
            conversation = await ConversationModel.get_conversation(conversation_id=conversation_id)
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Failed to retrieve conversation after creation"
                )
            
            return ConversationResponse(
                conversation_id=conversation["conversation_id"],
                participant_ids=conversation["participant_ids"],
                created_at=conversation["created_at"],
                last_updated=conversation["last_updated"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create conversation: {str(e)}"
            )