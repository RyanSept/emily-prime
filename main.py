import os

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.generators.utils import print_streaming_chunk
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.retrievers.pgvector import PgvectorEmbeddingRetriever
from haystack.telemetry import tutorial_running

from index_messages import get_store

tutorial_running(40)


if "OPENAI_API_KEY" not in os.environ:
    raise SystemError("OPENAI_API_KEY not found in environment variables.")

template = [
    ChatMessage.from_system("""
Your name is Ryan, the year is 2014. All you have in your memory are these documents in the store which are sourced from Whatsapp messages.
You cannot answer any questions based on your training data. You can only answer questions based on the given context below.
Answer the questions based on the given context.

Context:
{% for document in documents %}
    {{ document.content }}
{% endfor %}
Question: {{ question }}
Answer:
"""),
]
user_msg = "What is a list of your friends?"

rag_pipe = Pipeline()
rag_pipe.add_component("embedder", SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"))
rag_pipe.add_component("retriever", PgvectorEmbeddingRetriever(document_store=get_store(), top_k=3))
rag_pipe.add_component("prompt_builder", ChatPromptBuilder(template=template))
rag_pipe.add_component("llm", OpenAIChatGenerator(model="gpt-4o-mini", streaming_callback=print_streaming_chunk))

rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
rag_pipe.connect("retriever", "prompt_builder.documents")
rag_pipe.connect("prompt_builder.prompt", "llm.messages")

rag_pipe.run({"embedder": {"text": user_msg}, "prompt_builder": {"question": user_msg}})

# give better voice, LLM is still using default voice not Ryan
# Figure out how to give it understanding of entities
# Figure out how to get it to understand entities, how to be able to aggregate (sentiments, entities, etc)
# Ask LLM for design critique
