import os

if "OPENAI_API_KEY" not in os.environ:
    raise SystemError("OPENAI_API_KEY not found in environment variables.")

from itertools import chain
from typing import Any, List

from haystack import Pipeline, component
from haystack.components.builders import ChatPromptBuilder, PromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.generators.utils import print_streaming_chunk
from haystack.core.component.types import Variadic
from haystack.dataclasses import ChatMessage, ChatRole
from haystack_experimental.chat_message_stores.in_memory import InMemoryChatMessageStore
from haystack_experimental.components.retrievers import ChatMessageRetriever
from haystack_experimental.components.writers import ChatMessageWriter
from haystack_integrations.components.retrievers.pgvector import (
    PgvectorEmbeddingRetriever,
)
from haystack.telemetry import tutorial_running

from index_messages import get_store
from constants import MAIN_PROMPT_PATH

tutorial_running(40)


@component
class ListJoiner:
    def __init__(self, _type: Any):
        component.set_output_types(self, values=_type)

    def run(self, values: Variadic[Any]):
        result = list(chain(*values))
        return {"values": result}


with open(MAIN_PROMPT_PATH, "r") as f:
    system_message = ChatMessage.from_system(f.read())

query_rephrase_template = """
Rewrite the question for search while keeping its meaning and key terms intact.
If the conversation history is empty, DO NOT change the query.
Use conversation history user messages OR system messages only if necessary, and avoid extending the query with your own knowledge.
If no changes are needed, output the current question as is.

Conversation history:
-User messages-
{% for memory in memories %}
    {% if memory.role == 'user' %}
        {{ memory.text }}
    {% endif %}
{% endfor %}

User Query: {{query}}
Rewritten Query:
"""

# Memory components
memory_store = InMemoryChatMessageStore()
memory_retriever = ChatMessageRetriever(memory_store)
memory_writer = ChatMessageWriter(memory_store)

rag_pipe = Pipeline()

# Components for query rephrasing
rag_pipe.add_component(
    "query_rephrase_prompt_builder", PromptBuilder(query_rephrase_template)
)
rag_pipe.add_component("query_rephrase_llm", OpenAIGenerator())
rag_pipe.add_component(
    "list_to_str_adapter", OutputAdapter(template="{{ replies[0] }}", output_type=str)
)

# Components for RAG
rag_pipe.add_component(
    "embedder",
    SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"),
)
rag_pipe.add_component(
    # evaluate random sorting for retrieved documents
    "retriever",
    PgvectorEmbeddingRetriever(document_store=get_store()),
)
rag_pipe.add_component(
    "prompt_builder",
    ChatPromptBuilder(
        variables=["query", "documents", "memories"],
        required_variables=["query", "documents", "memories"],
    ),
)
rag_pipe.add_component(
    "llm",
    OpenAIChatGenerator(model="gpt-4o-mini", streaming_callback=print_streaming_chunk),
)

# Components for memory
rag_pipe.add_component("memory_retriever", memory_retriever)
rag_pipe.add_component("memory_writer", memory_writer)
rag_pipe.add_component("memory_joiner", ListJoiner(List[ChatMessage]))

# connections for query rephrasing
rag_pipe.connect("memory_retriever", "query_rephrase_prompt_builder.memories")
rag_pipe.connect("query_rephrase_prompt_builder.prompt", "query_rephrase_llm")
rag_pipe.connect("query_rephrase_llm.replies", "list_to_str_adapter")
rag_pipe.connect("list_to_str_adapter", "embedder.text")

# Connections for RAG
rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
rag_pipe.connect("retriever", "prompt_builder.documents")
rag_pipe.connect("prompt_builder.prompt", "llm.messages")

# Connections for memory
rag_pipe.connect("memory_joiner", "memory_writer")
rag_pipe.connect("memory_retriever", "prompt_builder.memories")
# write llm's own replies to in-chat memory
rag_pipe.connect("llm.replies", "memory_joiner.values")

rag_pipe.draw("data/pipeline.png")
print(rag_pipe)
# rag_pipe.run(
#     {"embedder": {"text": user_msg4}, "prompt_builder": {"question": user_msg4}}
#


DEBUG = False

while True:
    user_input = input("\nYou: ")
    if user_input == "/q":
        break
    if user_input.strip() == "":
        continue

    chat_user_msg = ChatMessage.from_user(user_input)
    messages = [system_message, chat_user_msg]

    res = rag_pipe.run(
        {
            "query_rephrase_prompt_builder": {"query": user_input},
            "prompt_builder": {"template": messages, "query": user_input},
            "memory_joiner": {"values": [chat_user_msg]},
        },
        include_outputs_from=[
            "llm",
            "query_rephrase_llm",
            "memory_writer",
            "retriever",
        ],
    )

    search_query = res["query_rephrase_llm"]["replies"][0]

    if DEBUG is True:
        print(f"\n   🔄 Memory Writer: {res['memory_writer']}")
        print(f"\n   📁 Retrieved Messages: {res['retriever']}")

    print(f"\n   🔎 Search Query: {search_query}")
