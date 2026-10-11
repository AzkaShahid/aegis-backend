
from app.services.ai_service import generate_response
from app.services.retrieval_service import (
    retrieve_relevant_chunks,
)

GENERAL_SYSTEM_PROMPT = """
You are Aegis, a helpful AI assistant.

Answer the user's question naturally and accurately.

Rules:
1. Be helpful and concise.
2. Do not pretend that information comes from documents when no document is selected.
3. For learning requests, explain concepts clearly and step by step when useful.
4. If the user wants English practice, act as an English conversation partner, tutor, and correction assistant.
"""



SYSTEM_PROMPT = """
You are Aegis, an AI document assistant.

Your job is to answer questions using the provided document context.

Rules:
1. Use the provided context as the primary source of truth.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information to answer,
   clearly say that the answer could not be found in the provided document.
4. Give a concise and clear answer.
5. When useful, refer to the document page number.
"""


async def answer_question(
    question: str,
    top_k: int = 5,
    document_id: int | None = None,
) -> dict:

    # ==================================================
    # GENERAL AI MODE
    # ==================================================

    if document_id is None:

        from app.services.ai_service import (
            generate_response,
        )

        messages = [
            {
                "role": "system",
                "content": GENERAL_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        answer = await generate_response(
            messages
        )

        return {
            "answer": answer,
            "sources": [],
        }


    # ==================================================
    # DOCUMENT RAG MODE
    # ==================================================

    chunks = await retrieve_relevant_chunks(
        query=question,
        top_k=top_k,
        document_id=document_id,
    )

    if not chunks:
        return {
            "answer": (
                "I couldn't find relevant information "
                "in the selected document."
            ),
            "sources": [],
        }

    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"""
Source: {chunk["filename"]}
Page: {chunk["page_number"]}

{chunk["content"]}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    user_prompt = f"""
Document context:

{context}

Question:

{question}

Answer the question using the document context above.
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    answer = await generate_response(
        messages
    )

    sources = [
        {
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page_number": chunk["page_number"],
            "similarity": chunk["similarity"],
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
    }


async def stream_answer(
    question: str,
    top_k: int = 5,
    document_id: int | None = None,
):
    """
    Stream either:

    1. General AI response when no document is selected.
    2. RAG response when a document is selected.
    """

    # ==================================================
    # GENERAL AI MODE
    # ==================================================

    if document_id is None:

        from app.services.ai_service import (
            stream_response,
        )

        yield {
            "type": "sources",
            "data": {
                "sources": [],
            },
        }

        messages = [
            {
                "role": "system",
                "content": GENERAL_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        async for token in stream_response(
            messages
        ):
            yield {
                "type": "token",
                "data": {
                    "content": token,
                },
            }

        return


    # ==================================================
    # DOCUMENT RAG MODE
    # ==================================================

    chunks = await retrieve_relevant_chunks(
        query=question,
        top_k=top_k,
        document_id=document_id,
    )

    if not chunks:

        yield {
            "type": "sources",
            "data": {
                "sources": [],
            },
        }

        yield {
            "type": "token",
            "data": {
                "content": (
                    "I couldn't find relevant information "
                    "in the selected document."
                ),
            },
        }

        return


    sources = [
        {
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page_number": chunk["page_number"],
            "similarity": chunk["similarity"],
        }
        for chunk in chunks
    ]


    yield {
        "type": "sources",
        "data": {
            "sources": sources,
        },
    }


    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"""
Source: {chunk["filename"]}
Page: {chunk["page_number"]}

{chunk["content"]}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    user_prompt = f"""
Document context:

{context}

Question:

{question}

Answer the question using the document context above.
"""


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


    from app.services.ai_service import (
        stream_response,
    )


    async for token in stream_response(
        messages
    ):
        yield {
            "type": "token",
            "data": {
                "content": token,
            },
        }

