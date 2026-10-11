
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.embedding_service import generate_embedding


async def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    document_id: int | None = None,
) -> list[dict]:
    """
    Find the most semantically relevant document chunks.

    If document_id is provided, search only within that document.
    Otherwise, search across all documents.
    """

    query = query.strip()

    if not query:
        return []

    query_embedding = generate_embedding(query)

    async with AsyncSessionLocal() as session:
        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        statement = (
            select(
                DocumentChunk,
                Document.filename,
                distance.label("distance"),
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                DocumentChunk.embedding.is_not(None)
            )
        )

        # Search only the selected document
        if document_id is not None:
            statement = statement.where(
                DocumentChunk.document_id == document_id
            )

        statement = (
            statement
            .order_by(distance)
            .limit(top_k)
        )

        result = await session.execute(statement)

        rows = result.all()

    retrieved_chunks = []

    for chunk, filename, distance_value in rows:
        similarity = 1.0 - float(distance_value)

        retrieved_chunks.append(
            {
                "document_id": chunk.document_id,
                "filename": filename,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "similarity": round(
                    similarity,
                    4,
                ),
            }
        )

    return retrieved_chunks

