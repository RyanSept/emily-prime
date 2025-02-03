import sqlite3
import datetime
import typing

from constants import WHATSAPP_DB_PATH


class WhatsappMessage(typing.TypedDict):
    _id: int
    text_data: str
    timestamp: int
    recipient: str


def _message_factory(cursor, row):
    """
    Return a dictionary where the keys are the column names and the values are the row values
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_whatsapp_messages_from_db(
    db_path: str = WHATSAPP_DB_PATH,
) -> typing.List[WhatsappMessage]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = _message_factory
    c = conn.cursor()

    MIN_TEXT_LENGTH = 30

    # only do <=2014 messages for now and limit to 100
    until = (
        int(datetime.datetime(2014, 12, 31, 23, 59, 59).timestamp()) * 1000
    )  # convert from unix to whatsapp timestamp
    query = f"""
    SELECT message._id, text_data, "jid".user as recipient, timestamp FROM  "message"
    -- join in order to get the recipient
    LEFT JOIN "chat" ON "message".chat_row_id = "chat"._id
    LEFT JOIN "jid" ON "chat".jid_row_id = "jid"._id
    -- only include messages I sent
    WHERE from_me=1
    AND timestamp < {until}
    AND LENGTH(text_data) - LENGTH(REPLACE(text_data, ' ', '')) + 1 > {MIN_TEXT_LENGTH}
    -- omit junk text
    AND NOT text_data LIKE "%               MERRY%"
    ORDER BY timestamp ASC;
    """
    c.execute(query)
    messages = c.fetchall()
    conn.close()
    return messages
