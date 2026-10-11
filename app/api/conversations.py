from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.conversation_service import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


class ConversationCreateRequest(BaseModel):
    document_id: int | None = None
    title: str = "New conversation"


@router.post("")
async def create(
    request: ConversationCreateRequest,
):
    conversation_id = await create_conversation(
        document_id=request.document_id,
        title=request.title,
    )

    return {
        "id": conversation_id,
    }


@router.get("")
async def list_all():
    return await list_conversations()


@router.get("/{conversation_id}")
async def get(
    conversation_id: int,
):
    conversation = await get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.delete("/{conversation_id}")
async def delete(
    conversation_id: int,
):
    deleted = await delete_conversation(
        conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }