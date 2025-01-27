import datetime

from haystack import Pipeline, Document
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore

from whatsapp_db import get_whatsapp_messages_from_db, WhatsappMessage
from contacts import get_contact_name

def get_store():
    document_store = PgvectorDocumentStore(
        table_name="test-ryan-2014-sentence-transformers-minilm",
        embedding_dimension=384,
        vector_function="cosine_similarity",
        recreate_table=False,
        search_strategy="hnsw"
    )
    return document_store

def index_and_store_whatsapp_messages(documents):
    document_store = get_store()

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component(
        instance=SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"), name="doc_embedder"
    )
    indexing_pipeline.add_component(instance=DocumentWriter(document_store=document_store), name="doc_writer")

    indexing_pipeline.connect("doc_embedder.documents", "doc_writer.documents")

    indexing_pipeline.run({"doc_embedder": {"documents": documents}})

def get_whatsapp_messages_as_docs() -> list[Document]:
    messages = get_whatsapp_messages_from_db()
    docs = []
    for message in messages:
        message = enrich_message(message)
        doc = Document(id=message["_id"], content=message["text_data"], meta={"timestamp": message["timestamp"]})
        docs.append(doc)
    return docs

def enrich_message(message: WhatsappMessage) -> WhatsappMessage:
    "Label message text with recipient name and date"
    contact_name = get_contact_name(message["recipient"])
    time = datetime.datetime.fromtimestamp(message["timestamp"] / 1000).strftime("%I:%M%p, %d %B %Y")
    message["text_data"] = f"{time}, to {contact_name}: {message['text_data']}"
    return message

if __name__ == "__main__":
    index_and_store_whatsapp_messages(get_whatsapp_messages_as_docs())
# index_and_store_whatsapp_messages(get_whatsapp_messages_as_docs())
