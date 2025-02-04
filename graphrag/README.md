## Populate input data

```bash
python populate_input_files.py
graphrag prompt-tune --domain "my text messages" --selection-method auto --limit 10 --language English --max-tokens 2048 --chunk-size 256 --min-examples-required 3
graphrag query --method global --query "Who is Ryan?"
```
