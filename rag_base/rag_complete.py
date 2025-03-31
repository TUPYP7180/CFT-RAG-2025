import os
import time
import tiktoken
from typing import Iterable

from lab_1806_vec_db import RagMultiVecDB, RagVecDB
from openai import OpenAI

from rag_base.embed_model import get_embed_model
from trag_tree import EntityTree
from entity import ruler
from sentence_transformers import SentenceTransformer, util
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


# 对树节点上下文进行相关度排序
def rank_contexts(query: str, contexts: list, rank_k : int) -> list:
    
    model = SentenceTransformer('all-MiniLM-L6-v2')  
    query_embedding = model.encode(query, convert_to_tensor=True)
    context_embeddings = model.encode(contexts, convert_to_tensor=True)
    
    similarities = util.pytorch_cos_sim(query_embedding, context_embeddings)[0]
    
    top_indices = similarities.argsort(descending=True).tolist()
    ranked_contexts = []
    seen_embeddings = []
    
    for idx in top_indices:
        context = contexts[idx]
        context_embedding = context_embeddings[idx]
        
        # 计算与已选上下文的相似度，去除高度相似的项
        if any(util.pytorch_cos_sim(context_embedding, emb) > 0.9 for emb in seen_embeddings):
            continue
        
        ranked_contexts.append(context)
        seen_embeddings.append(context_embedding)
        
        if len(ranked_contexts) == rank_k:
            break
    
    return ranked_contexts


retrieval_time = None
generation_time = None

def augment_prompt(query: str, db: RagVecDB | RagMultiVecDB, forest: list[EntityTree]=None, nlp=None, search_method=1, k=3, model_name="gpt-3.5-turbo", debug=False):
    global retrieval_time
    
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
        node_list = list(node_list.split("**CUK**"))
    elif search_method in [8, 9]:
        node_list = ruler.search_entity_info_ann(nlp, query)
    
    # print(f"\nlength of node_list: {len(node_list)}")    
    
    if search_method != 7:
        node_list = [c.get_context() for c in node_list if c is not None]

    print(f"query entity number: {ruler.entity_number}")

    node_list = rank_contexts(query, node_list, ruler.entity_number)
    
    tree_knowledge = "\n---\n".join(node_list)

    end_time = time.time()
    # tree_knowledge = tree_knowledge[:64000]
    
    # max_allowed_tokens = (int)((MAX_TOKENS - 500) / 2)
    # source_knowledge = truncate_to_fit(source_knowledge, max_allowed_tokens, model_name)
    # tree_knowledge = truncate_to_fit(tree_knowledge, max_allowed_tokens, model_name)

    augmented_prompt = (
        f"请回答问题，可以使用我提供的信息（不保证信息是有用的），在回答中不要有分析我提供信息的内容，直接说答案，答案要简略。\n\n信息:\n{source_knowledge}\n\n关系：\n{tree_knowledge}\n\n问题: \n{query}"
    )

    execution_time = end_time - start_time
    retrieval_time = execution_time

    if debug:
        print(f"\n\033[1;31mEntity retrieval time: {execution_time:.6f} seconds\033[0m\n")
        # print(f"\n\nsource_knowledge: {source_knowledge}")
        # print(f"augmented_prompt: {augmented_prompt}")
    return augmented_prompt

client = OpenAI(
    api_key = os.environ.get("ARK_API_KEY"),
    base_url = "https://ark.cn-beijing.volces.com/api/v3",
)

def rag_complete(
    prompt: str,
    db: RagVecDB | RagMultiVecDB,
    forest: list[EntityTree]=None,
    nlp=None,
    search_method=1,
    model_name: str | None = None,
    debug=False,
) -> Iterable[str]:
    
    global retrieval_time
    global generation_time

    client = OpenAI(
        api_key = os.environ.get("ARK_API_KEY"),
        base_url = "https://ark.cn-beijing.volces.com/api/v3",
    )

    model_name = model_name or get_model_name()

    start_time = time.time()

    stream = client.chat.completions.create(
        model = "your model",
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

    end_time = time.time()

    generation_time = end_time - start_time

    print(f"\n\033[1;31mTime Ratio: {(retrieval_time*100.0)/(retrieval_time+generation_time):.6f}%\033[0m")
