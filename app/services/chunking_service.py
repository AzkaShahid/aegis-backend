import re


def clean_text(text: str) -> str:
    """
    Normalize whitespace while preserving paragraph boundaries.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    """
    Split a document into paragraphs using blank lines.

    This is document-agnostic and does not depend on
    specific section names.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(
        r"\n\s*\n",
        text,
    )

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def split_long_text(
    text: str,
    chunk_size: int = 180,
    overlap: int = 40,
) -> list[str]:
    """
    Split a long paragraph into overlapping
    word-based chunks.
    """

    words = text.split()

    if not words:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 180,
    overlap: int = 40,
) -> list[str]:
    """
    Create semantic-ish chunks by preserving paragraphs
    whenever possible and splitting only when necessary.

    This function is document-agnostic.
    """

    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return []

    chunks = []
    current_words = []

    for paragraph in paragraphs:

        paragraph_words = paragraph.split()

        # --------------------------------------------------
        # Very large paragraph
        # --------------------------------------------------

        if len(paragraph_words) > chunk_size:

            # Flush existing content first
            if current_words:
                chunks.append(
                    " ".join(current_words)
                )

                current_words = []

            large_chunks = split_long_text(
                paragraph,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            chunks.extend(
                large_chunks
            )

            continue

        # --------------------------------------------------
        # Adding this paragraph would exceed chunk size
        # --------------------------------------------------

        if (
            current_words
            and len(current_words)
            + len(paragraph_words)
            > chunk_size
        ):
            chunks.append(
                " ".join(current_words)
            )

            # Keep a small word overlap from
            # the previous chunk.
            if overlap > 0:
                current_words = current_words[
                    -overlap:
                ]
            else:
                current_words = []

        current_words.extend(
            paragraph_words
        )

    # --------------------------------------------------
    # Flush final chunk
    # --------------------------------------------------

    if current_words:
        chunks.append(
            " ".join(current_words)
        )

    return [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 180,
    overlap: int = 40,
) -> list[dict]:
    """
    Create page-aware, document-agnostic chunks.
    """

    chunks = []
    chunk_id = 1

    for page in pages:

        page_number = page["page_number"]
        page_text = page["text"]

        if not page_text.strip():
            continue

        page_chunks = chunk_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for text in page_chunks:

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "page_number": page_number,
                    "text": text,
                }
            )

            chunk_id += 1

    return chunks