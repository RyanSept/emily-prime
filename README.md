# Emily Prime

<img src="./docs/emily-prime.jpeg" width=600 />

## Install

```bash
uv pip install
```

## Start Server

```bash
letta server
```

## Set up pgvector

```bash
brew install pgvector
psql postgres
postgres=# CREATE EXTENSION vector;
# CREATE EXTENSION
```

## Create the table and index all messages

This command will get all the messages from the Whatsapp DB, generate their embeddings and insert them into a pgvector table

```sh
python index_messages.py
```

## Start chat session

```sh
python main.py
```
