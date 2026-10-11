import pymupdf


def extract_pdf_text(file_path: str) -> dict:
    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(
        document,
        start=1,
    ):
        text = page.get_text(
            "text",
            sort=True,
        ).strip()

        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

    document.close()

    full_text = "\n\n".join(
        page["text"]
        for page in pages
        if page["text"]
    )

    return {
        "page_count": len(pages),
        "text": full_text,
        "pages": pages,
    }