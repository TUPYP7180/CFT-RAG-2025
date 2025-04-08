import os

from sentence_transformers import SentenceTransformer

embed_model_cache: dict[str, SentenceTransformer] = {}


def get_embed_model():
    embed_model_name = (
        os.getenv("EMBED_MODEL_NAME") or "sentence-transformers/all-MiniLM-L6-v2"
    )
    if embed_model_name in embed_model_cache:
        return embed_model_cache[embed_model_name]

    embed_model = SentenceTransformer(embed_model_name)
    embed_model_cache[embed_model_name] = embed_model
    return embed_model
