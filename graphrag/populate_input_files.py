import sys

# setting path
sys.path.append('..')

from index_messages import get_whatsapp_messages_as_docs
from constants import ROOT_DIR

INPUT_FILE = f"{ROOT_DIR}/graphrag/input/messages.txt"

# create a text file in input inserting each message on a line
def populate_input_file():
    messages = get_whatsapp_messages_as_docs()

    with open(INPUT_FILE, 'w') as f:
        for message in messages:
            f.write(message.content + '\n\n')

if __name__ ==  """__main__""":
    populate_input_file()
    print(f"Populated {INPUT_FILE} with messages from the database.")
