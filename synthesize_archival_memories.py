# 1. Query SQLIte database for messages
# 2. Dump messages into text files
# 3. create_source for agent
# 4. Ingest text files into database
# 4. figure out how to include date

import sqlite3
import datetime
import typing

from letta import Passage, create_client, RESTClient, AgentState
from letta.agent_store.storage import StorageConnector, TableType
from letta.config import LettaConfig
from letta.embeddings import embedding_model

from constants import WHATSAPP_DB_PATH, TEST_RYAN_2014

SOURCE_NAME = "whatsapp"

def message_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class WhatsappMessage(typing.TypedDict):
    _id: int
    text_data: str
    timestamp: int

def get_whatsapp_messages_from_db(db_path) -> typing.List[WhatsappMessage]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = message_factory
    c = conn.cursor()

    MIN_TEXT_LENGTH = 30

    until  = int(datetime.datetime(2014, 12, 31, 23, 59, 59).timestamp()) * 1000  # convert from unix to whatsapp timestamp
    # before 2015
    query = f"""
    SELECT _id, text_data, timestamp FROM  "message"
    WHERE from_me=1
    AND timestamp < {until}
    AND LENGTH(text_data) - LENGTH(REPLACE(text_data, ' ', '')) + 1 > {MIN_TEXT_LENGTH}
    ORDER BY timestamp ASC
    LIMIT 100;
    """
    c.execute(query)
    messages = c.fetchall()
    conn.close()
    return messages

def get_or_create_source(name: str, client: RESTClient, agent: AgentState):
    try:
        return client.get_source(client.get_source_id(name))
    except AttributeError:
        return client.create_source(name, agent.embedding_config)

def store_in_archival_memory(messages: typing.List[WhatsappMessage]):
    # obtain storageconnector for archival memory
    config = LettaConfig.load()
    user_id = "ryan-conn"
    conn = StorageConnector.get_storage_connector(TableType.ARCHIVAL_MEMORY, config, user_id, agent_id=TEST_RYAN_2014)

    client = create_client(base_url="http://localhost:8283")
    agent = client.get_agent(agent_id=TEST_RYAN_2014)
    whatsapp_source = get_or_create_source(SOURCE_NAME, client, agent)
    print(whatsapp_source)

    embed_model = embedding_model(agent.embedding_config)

    passages = []

    for message in messages:
        # create passage object
        embeddings = embed_model.get_text_embedding(message["text_data"])
        passage = Passage(
            text=message["text_data"],
            embedding=embeddings,
            embedding_config=agent.embedding_config,
            created_at=datetime.datetime.fromtimestamp(message["timestamp"] / 1000),
            user_id=agent.user_id,
            agent_id=agent.id,
            source_id=whatsapp_source.id,
            file_id=str(message["_id"]),
        )
        print(passage)
        passages.append(passage)
    conn.insert_many(passages)
    conn.save()

    size = conn.size()
    client.attach_source_to_agent(whatsapp_source.id, agent.id)
    print("Number of passages", size)

messages = get_whatsapp_messages_from_db(WHATSAPP_DB_PATH)
print(messages)
print("#\n"*30)
store_in_archival_memory(messages)
