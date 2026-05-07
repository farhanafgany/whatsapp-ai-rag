import csv
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_PATH = Path("data")
CHROMA_PATH = "chroma_db"

_vectorstore: Chroma | None = None


def _load_documents() -> list[Document]:
    docs = []

    for md_file in DATA_PATH.glob("*.md"):
        docs.append(Document(
            page_content=md_file.read_text(encoding="utf-8"),
            metadata={"source": md_file.name},
        ))

    with open(DATA_PATH / "produk.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            content = (
                f"Produk: {row['nama_produk']}\n"
                f"Kategori: {row['kategori']}\n"
                f"Brand: {row['brand']}\n"
                f"Model: {row['model']}\n"
                f"Harga: ${row['harga_usd']}\n"
                f"Stok: {row['stok']} unit\n"
                f"Deskripsi: {row['deskripsi']}"
            )
            docs.append(Document(
                page_content=content,
                metadata={"source": "produk.csv", "product_id": row["id"]},
            ))

    return docs


def _build_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    chroma_db_file = Path(CHROMA_PATH) / "chroma.sqlite3"
    if chroma_db_file.exists():
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    docs = _load_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = _build_vectorstore()
    return _vectorstore


def retrieve(query: str, k: int = 5) -> str:
    docs = get_vectorstore().similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in docs)
