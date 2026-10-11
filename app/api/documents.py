
from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.models.chunk import DocumentChunk

from app.services.document_service import extract_pdf_text
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import generate_embeddings


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


# ==================================================
# Upload Document
# ==================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload a PDF, extract text, create chunks,
    generate embeddings, and store everything
    in PostgreSQL.
    """

    # --------------------------------------------------
    # 1. Validate uploaded file
    # --------------------------------------------------

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    filename = file.filename or ""

    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only .pdf files are supported.",
        )

    temporary_path = None

    try:
        # --------------------------------------------------
        # 2. Save PDF temporarily
        # --------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

            temporary_path = temporary_file.name

        # --------------------------------------------------
        # 3. Extract PDF text
        # --------------------------------------------------

        document_data = extract_pdf_text(
            temporary_path
        )

        # --------------------------------------------------
        # 4. Create chunks
        # --------------------------------------------------

        chunks = chunk_pages(
            document_data["pages"]
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="The PDF contains no extractable text.",
            )

        # --------------------------------------------------
        # 5. Generate embeddings
        # --------------------------------------------------

        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = generate_embeddings(
            chunk_texts
        )

        # --------------------------------------------------
        # 6. Save document + chunks
        # --------------------------------------------------

        async with AsyncSessionLocal() as session:

            document = Document(
                filename=filename,
                content_type=file.content_type,
                page_count=document_data["page_count"],
            )

            session.add(document)

            # Generate document ID
            await session.flush()

            document_chunks = []

            for index, (
                chunk,
                embedding,
            ) in enumerate(
                zip(chunks, embeddings)
            ):

                document_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    page_number=chunk["page_number"],
                    content=chunk["text"],
                    embedding=embedding,
                )

                document_chunks.append(
                    document_chunk
                )

            session.add_all(
                document_chunks
            )

            await session.commit()

            document_id = document.id

        # --------------------------------------------------
        # 7. Return result
        # --------------------------------------------------

        return {
            "message": "Document uploaded successfully.",
            "document_id": document_id,
            "filename": filename,
            "page_count": document_data["page_count"],
            "text_length": len(document_data["text"]),
            "chunk_count": len(chunks),
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Document processing error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process PDF.",
        )

    finally:
        # --------------------------------------------------
        # 8. Delete temporary PDF
        # --------------------------------------------------

        if temporary_path:
            Path(temporary_path).unlink(
                missing_ok=True
            )

        await file.close()


# ==================================================
# List Documents
# ==================================================

@router.get("")
async def list_documents():
    """
    Return all uploaded documents.
    """

    try:
        async with AsyncSessionLocal() as session:

            statement = (
                select(Document)
                .order_by(
                    Document.created_at.desc()
                )
            )

            result = await session.execute(
                statement
            )

            documents = result.scalars().all()

            return [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "content_type": document.content_type,
                    "page_count": document.page_count,
                    "created_at": document.created_at,
                }
                for document in documents
            ]

    except Exception as error:
        print(
            "Document listing error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documents.",
        )


# ==================================================
# Delete Document
# ==================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
):
    """
    Delete a document and its associated chunks.
    """

    try:
        async with AsyncSessionLocal() as session:

            statement = select(Document).where(
                Document.id == document_id
            )

            result = await session.execute(
                statement
            )

            document = (
                result.scalar_one_or_none()
            )

            if document is None:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            await session.delete(document)

            await session.commit()

            return {
                "message": (
                    "Document deleted successfully."
                ),
                "document_id": document_id,
            }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Document deletion error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document.",
        )

