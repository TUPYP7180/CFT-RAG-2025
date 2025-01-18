import os
import time
import tiktoken
from typing import Iterable

from lab_1806_vec_db import RagMultiVecDB, RagVecDB
from openai import OpenAI

from src.embed_model import get_embed_model
from trag_tree import EntityTree
from entity import ruler

import tiktoken

MAX_TOKENS = 16385

# 限制字符串长度
def truncate_to_fit(text, max_tokens, model_name):
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return encoding.decode(tokens)


def get_model_name():
    return os.getenv("MODEL_NAME") or "gpt-4o-mini"


def augment_prompt(query: str, db: RagVecDB | RagMultiVecDB, forest: list[EntityTree]=None, nlp=None, search_method=1, k=3, model_name="gpt-3.5-turbo", debug=False):
    embed_model = get_embed_model()
    
    start_time = time.time()
    input_embedding: list[float] = embed_model.encode([query])[0].tolist()
    results = db.search(input_embedding, k)
    end_time = time.time()
    if debug:
        execution_time = end_time - start_time
        # print(f"\n\033[1;31mVectorDB search time: {execution_time:.6f} seconds\033[0m\n")
        # print(f"Search with {k=}, {query=}; Got {len(results)} results")
        # for idx, r in enumerate(results):
        #     title = r["title"]
        #     print(f"{idx}: {title=}")

    source_knowledge = "\n".join([x["content"] for x in results])

    if forest is None or search_method == 0:
        # max_allowed_tokens = MAX_TOKENS - 500
        # source_knowledge = truncate_to_fit(source_knowledge, max_allowed_tokens, model_name)
        augmented_prompt = (
            f"使用提供的信息回答问题。\n\n信息:\n{source_knowledge}\n\n问题: \n{query}"
        )
        if debug:
            # print(f"augmented_prompt: {augmented_prompt}")
            pass
        return augmented_prompt

    node_list = []
    
    start_time = time.time()
    
    if search_method in [1, 2, 5, 6]:
        for entity_tree in forest:
            node_list += ruler.search_entity_info(entity_tree, nlp, query, search_method)
    elif search_method == 4:
        node_list = ruler.search_entity_info_naive_hash(nlp, query)
    elif search_method == 7:
        node_list = ruler.search_entity_info_cuckoofilter(nlp, query)
    
        
    # print(f"\nlength of node_list: {len(node_list)}")
        
    end_time = time.time()
    
    if search_method != 7:
        tree_knowledge = "\n".join([c.get_context() for c in node_list if c is not None])
    else:
        tree_knowledge = node_list
        
    tree_knowledge = tree_knowledge[:64000]
    
    # max_allowed_tokens = (int)((MAX_TOKENS - 500) / 2)
    # source_knowledge = truncate_to_fit(source_knowledge, max_allowed_tokens, model_name)
    # tree_knowledge = truncate_to_fit(tree_knowledge, max_allowed_tokens, model_name)

    augmented_prompt = (
        f"使用提供的信息和树形层级关系回答问题，树形层级关系的各个节点不一定都要使用。\n\n信息:\n{source_knowledge}\n\n树形层级关系：\n{tree_knowledge}\n\n问题: \n{query}"
    )
    if debug:
        execution_time = end_time - start_time    
        print(f"\n\033[1;31mEntityTree search time: {execution_time:.6f} seconds\033[0m\n")
        # print(f"\n\nsource_knowledge: {source_knowledge}")
        # print(f"augmented_prompt: {augmented_prompt}")
    return augmented_prompt


def rag_complete(
    prompt: str,
    db: RagVecDB | RagMultiVecDB,
    forest: list[EntityTree]=None,
    nlp=None,
    search_method=1,
    model_name: str | None = None,
    debug=False,
) -> Iterable[str]:
    model_name = model_name or get_model_name()
    stream = OpenAI().chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. You should use the same language as the user.",
            },
            {
                "role": "user",
                "content": augment_prompt(prompt, db, forest, nlp, search_method=search_method, model_name=model_name, debug=debug),
            },
        ],
        stream=True,
    )
    for chunk in stream:
        choices = chunk.choices
        if len(choices) == 0:
            break
        content = choices[0].delta.content
        if content is not None:
            yield content
