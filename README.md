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

## Generate Archival memories and attach to agent

```bash
python synthesize_archival_memories.py
```
