# CFT-RAG-2025
CFT-RAG: An Entity Tree Based Retrieval Augmented Generation Algorithm With Cuckoo Filter

# Notice

`TRAG-cuckoofilter` is based on https://github.com/efficient/cuckoofilter.

# Deploy

python version: 3.10

API key is needed.

```
pip install uv
uv sync
pip install lab-1806-vec-db==0.2.3 spacy python-dotenv sentence-transformers openai pybloom_live tiktoken
export HF_ENDPOINT=https://hf-mirror.com
python -m spacy download zh_core_web_sm
```

# Test

## Complete Process of RAG

Arguments:

* `vec-db-key`: The key for the vector database.
* `tree-num-max`: The maximum number of trees to build.
* `entities-file-name`: The name of the entities file.
* `search-method`: The search method to use: 0 for no tree, 1 for BFS, 2 for BloomFilter Search, 5 for improved BloomFilter Search, 6 for improved BloomFilter-Cpp Search, 7 for Cuckoo filter.
* `node-num-max`: The maximum number of nodes to build.

Example: 

```
python main.py --tree-num-max 50 --search-method 7
```

## Test Cuckoofilter

Individually testing the performance of the improved Cuckoofilter and the sorting results:

```
python test_tree.py
```
