from app.services.chunking_service import chunk_text


text = """
Federated learning allows multiple devices to collaboratively
train a machine learning model without sending their raw data
to a central server.
"""


chunks = chunk_text(
    text,
    chunk_size=20,
    overlap=5,
)


for index, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {index} ---")
    print(chunk)