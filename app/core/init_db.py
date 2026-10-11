from sqlalchemy import text

from app.core.database import engine
from app.models.document import Base
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage

async def init_db():
    async with engine.begin() as connection:

        # Enable pgvector
        await connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )

        # Create all tables
        await connection.run_sync(
            Base.metadata.create_all
        )