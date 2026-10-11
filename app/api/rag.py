
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from fastapi.responses import StreamingResponse
from app.services.rag_service import (
    answer_question,
    stream_answer,
)
from app.services.conversation_service import (
    add_message,
    create_conversation,
    get_conversation,
)

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"],
)

class RAGRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: int | None = None
    conversation_id: int | None = None


class Source(BaseModel):
    document_id: int
    filename: str
    page_number: int
    similarity: float


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    
@router.post("/stream")
async def rag_stream(
    request: RAGRequest,
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if request.top_k < 1 or request.top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10.",
        )

    async def event_generator():
        try:
            conversation_id = (
                request.conversation_id
            )

            # ------------------------------------------
            # Create conversation if this is a new chat
            # ------------------------------------------

            if conversation_id is None:
                conversation_id = (
                    await create_conversation(
                        document_id=request.document_id,
                        title=question[:80],
                    )
                )
            else:
                conversation = (
                    await get_conversation(
                        conversation_id
                    )
                )

                if conversation is None:
                    yield (
                        "event: error\n"
                        "data: {"
                        "\"message\":\"Conversation not found.\""
                        "}\n\n"
                    )
                    return

            # ------------------------------------------
            # Save user message
            # ------------------------------------------

            await add_message(
                conversation_id=conversation_id,
                role="user",
                content=question,
            )

            # Tell frontend which conversation we're using
            yield (
                "event: conversation\n"
                f"data: {json.dumps({
                    'conversation_id': conversation_id
                })}\n\n"
            )

            assistant_parts = []
            sources = []

            # ------------------------------------------
            # Retrieve + stream answer
            # ------------------------------------------

            async for event in stream_answer(
                question=question,
                top_k=request.top_k,
                document_id=request.document_id,
            ):

                if event["type"] == "sources":
                    sources = event["data"].get(
                        "sources",
                        [],
                    )

                if event["type"] == "token":
                    assistant_parts.append(
                        event["data"].get(
                            "content",
                            "",
                        )
                    )

                yield (
                    f"event: {event['type']}\n"
                    f"data: {json.dumps(event['data'])}\n\n"
                )

            # ------------------------------------------
            # Save complete assistant answer
            # ------------------------------------------

            assistant_answer = "".join(
                assistant_parts
            )

            if assistant_answer:
                await add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_answer,
                    sources=sources,
                )

            yield (
                "event: done\n"
                "data: {}\n\n"
            )

        except Exception as error:
            print(
                "RAG streaming error:",
                repr(error),
            )

            yield (
                "event: error\n"
                f"data: {json.dumps({
                    'message': 'Failed to generate response.'
                })}\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
@router.post("", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if request.top_k < 1 or request.top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10.",
        )

    try:
        result = await answer_question(
            question=question,
            top_k=request.top_k,
            document_id=request.document_id,
        )

        return RAGResponse(
            question=question,
            answer=result["answer"],
            sources=result["sources"],
        )

    except Exception as error:
        print(
            "RAG error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate RAG response.",
        )

