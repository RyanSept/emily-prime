import sqlite3
import datetime
import typing

from constants import WHATSAPP_DB_PATH

class WhatsappMessage(typing.TypedDict):
    _id: int
    text_data: str
    timestamp: int

def _message_factory(cursor, row):
    """
    Return a dictionary where the keys are the column names and the values are the row values
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_whatsapp_messages_from_db(db_path: str = WHATSAPP_DB_PATH) -> typing.List[WhatsappMessage]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = _message_factory
    c = conn.cursor()

    MIN_TEXT_LENGTH = 30

    # only do <=2014 messages for now and limit to 100
    until  = int(datetime.datetime(2014, 12, 31, 23, 59, 59).timestamp()) * 1000  # convert from unix to whatsapp timestamp
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

# messages = get_whatsapp_messages_from_db(WHATSAPP_DB_PATH)
# print(messages)
# print("#\n"*30)
