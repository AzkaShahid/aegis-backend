from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.conversation_message import (
    ConversationMessage,
)


async def create_conversation(
    document_id: int | None = None,
    title: str = "New conversation",
) -> int:
    async with AsyncSessionLocal() as session:
        conversation = Conversation(
            title=title[:255],
            document_id=document_id,
        )

        session.add(conversation)

        await session.flush()

        conversation_id = conversation.id

        await session.commit()

        return conversation_id


async def add_message(
    conversation_id: int,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        conversation = await session.get(
            Conversation,
            conversation_id,
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found."
            )

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )

        session.add(message)

        conversation.updated_at = (
            datetime.now(timezone.utc)
        )

        await session.commit()


async def get_conversation(
    conversation_id: int,
) -> dict | None:
    async with AsyncSessionLocal() as session:
        conversation = await session.get(
            Conversation,
            conversation_id,
        )

        if conversation is None:
            return None

        statement = (
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id
                == conversation_id
            )
            .order_by(
                ConversationMessage.created_at.asc()
            )
        )

        result = await session.execute(
            statement
        )

        messages = result.scalars().all()

        return {
            "id": conversation.id,
            "title": conversation.title,
            "document_id": conversation.document_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "sources": message.sources or [],
                    "created_at": message.created_at,
                }
                for message in messages
            ],
        }


async def list_conversations(
    limit: int = 50,
) -> list[dict]:
    async with AsyncSessionLocal() as session:
        statement = (
            select(Conversation)
            .order_by(
                Conversation.updated_at.desc()
            )
            .limit(limit)
        )

        result = await session.execute(
            statement
        )

        conversations = result.scalars().all()

        return [
            {
                "id": conversation.id,
                "title": conversation.title,
                "document_id": conversation.document_id,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            }
            for conversation in conversations
        ]


async def delete_conversation(
    conversation_id: int,
) -> bool:
    async with AsyncSessionLocal() as session:
        conversation = await session.get(
            Conversation,
            conversation_id,
        )

        if conversation is None:
            return False

        await session.delete(
            conversation
        )

        await session.commit()

        return True