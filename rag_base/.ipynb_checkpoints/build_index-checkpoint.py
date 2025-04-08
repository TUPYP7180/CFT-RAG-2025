import os

from lab_1806_vec_db import RagVecDB
from tqdm.autonotebook import tqdm

from src.embed_model import get_embed_model


def split_string_by_headings(text: str):
    lines = text.split("\n")
    current_block: list[str] = []
    chunks: list[str] = []

    def concat_block():
        if len(current_block) > 0:
            chunks.append("\n".join(current_block))
            current_block.clear()

    for line in lines:
        if line.startswith("# "):
            concat_block()
        current_block.append(line)
    concat_block()
    return chunks


def collect_chunks_from_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()
        return split_string_by_headings(data)


def collect_chunks_from_dir(dir: str):
    chunks: list[str] = []
    for filename in os.listdir(dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(dir, filename)
            chunks.extend(collect_chunks_from_file(file_path))
    return chunks


def collect_chunks(dir_or_file: str):
    if os.path.isdir(dir_or_file):
        return collect_chunks_from_dir(dir_or_file)
    return collect_chunks_from_file(dir_or_file)


def build_index_on_chunks(chunks: list[str], batch_size: int = 100):
    batch_size = 64
    model = get_embed_model()
    dim = model.get_sentence_embedding_dimension()
    assert isinstance(dim, int), "Cannot get embedding dimension"

    db = RagVecDB(dim)

    for i in tqdm(range(0, len(chunks), batch_size)):
        i_end = min(len(chunks), i + batch_size)
        content = chunks[i:i_end]
        title = [content.split("\n")[0] for content in content]
        vecs = model.encode(title, normalize_embeddings=True)
        db.batch_add(
            vecs.tolist(),
            [
                {"content": content, "title": title}
                for title, content in zip(title, content)
            ],
        )

    return db


vec_db_cache_dir = "vec_db_cache/"


def ensure_vec_db_cache_dir():
    if not os.path.exists(vec_db_cache_dir):
        os.mkdir(vec_db_cache_dir)


def cache_path_for_key(key: str):
    ensure_vec_db_cache_dir()
    return os.path.join(vec_db_cache_dir, f"{key}.db")


def load_vec_db(key: str, dir_or_file: str):
    index_path = cache_path_for_key(key)
    if os.path.exists(index_path):
        return RagVecDB.load(index_path)

    chunks = collect_chunks(dir_or_file)
    db = build_index_on_chunks(chunks)
    db.save(index_path)
    return db
