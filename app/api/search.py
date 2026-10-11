from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.retrieval_service import (
    retrieve_relevant_chunks,
)


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    chunk_index: int
    page_number: int
    content: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@router.post("", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if request.top_k < 1 or request.top_k > 20:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 20.",
        )

    try:
        chunks = await retrieve_relevant_chunks(
            query=query,
            top_k=request.top_k,
        )

        return SearchResponse(
            query=query,
            results=chunks,
        )

    except Exception as error:
        print(
            "Semantic search error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to perform semantic search.",
        )