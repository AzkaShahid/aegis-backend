from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_service import generate_response


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
        ]

        response = await generate_response(messages)

        return ChatResponse(
            response=response
        )

    except Exception as error:
        print("AI REQUEST ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail=repr(error),
        )