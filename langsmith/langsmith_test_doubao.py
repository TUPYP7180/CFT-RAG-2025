### RAG

import openai
from langsmith import traceable
from langsmith.wrappers import wrap_openai

import os

from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


from dotenv import load_dotenv
from src.build_index import load_vec_db
from src.rag_complete import augment_prompt
from trag_tree import build, hash
import time
import argparse

load_dotenv()

# example: python langsmith_test_doubao.py  --tree-num-max 50 --search-method 7
parser = argparse.ArgumentParser(description="Parse input arguments for RAG system.")
parser.add_argument('--vec-db-key', type=str, default="院志", help="The key for the vector database.")
parser.add_argument('--tree-num-max', type=int, default=50, help="The maximum number of trees to build.")
parser.add_argument('--entities-file-name', type=str, default="entities_file", help="The name of the entities file.")
parser.add_argument('--search-method', type=int, default=1, choices=[0, 1, 2, 4, 5, 6, 7], 
                    help="The search method to use: 0 for no tree, 1 for BFS, 2 for BloomFilter Search, 4 for simple hash, 5 for improved BloomFilter Search, 6 for improved BloomFilter-Cpp Search, 7 for Cuckoo filter.")
parser.add_argument('--node-num-max', type=int, default=2000000, help="The maximum number of nodes to build.")

args = parser.parse_args()

vec_db_key = args.vec_db_key
tree_num_max = args.tree_num_max
entities_file_name = args.entities_file_name
search_method = args.search_method
node_num_max = args.node_num_max

start_time = time.time()

vec_db = load_vec_db(vec_db_key, "vec_db_cache/")
print("Load vector db finished")

forest, nlp = build.build_forest(tree_num_max, entities_file_name, search_method, node_num_max)
print("Load forest and nlp finished")

if search_method in [4]:
    for entity_tree in forest:
        entity_tree.bfs_hash()

if search_method in [7]:
    hash.cuckoo_build(tree_num_max, node_num_max)


# if search_method == 7:
#     hash.cuckoo_sort()
#     print("try to retrieve after sorting")


score_total = 0

class RagBot:
    
    def __init__(self,  model: str = "ep-20241101151030-lfwks"):
        # self._retriever = retriever
        # Wrapping the client instruments the LLM
        self._client = client
        self._model = model

    # @traceable()
    def retrieve_docs(self, question):
        # return self._retriever.invoke(question)
        return augment_prompt(question, vec_db, forest, nlp, search_method=search_method, model_name=self._model, debug=True),

    # @traceable()
    def get_answer(self, question: str):
        similar = self.retrieve_docs(question)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个了解医院历史信息的资深专家，接下来我会告诉你一些信息，用中文回答",
                },
                {"role": "user", "content": question},
            ],
        )
        # print(f"response.choices[0].message.content:{response.choices[0].message.content}")
        # Evaluators will expect "answer" and "contexts"
        return {
            "answer": response.choices[0].message.content,
            "contexts": [str(doc) for doc in similar],
        }
    
    
rag_bot = RagBot()


# RAG chain
def predict_rag_answer(example: dict):
    """Use this for answer evaluation"""
    # print(f"Example: {example}")
    response = rag_bot.get_answer(example["prompt"])
    return {"answer": response["answer"]}

def predict_rag_answer_with_context(example: dict):
    """Use this for evaluation of retrieved documents and hallucinations"""
    response = rag_bot.get_answer(example["prompt"])
    return {"answer": response["answer"], "contexts": response["contexts"]}

from langsmith.evaluation import LangChainStringEvaluator, evaluate

from langsmith.schemas import Example, Run

def custom_score_match(run: Run, example: Example) -> dict:
    reference = example.outputs["answer"]
    prediction = run.outputs["answer"]
    
    # score = prediction.lower() == reference.lower()
    completion = client.chat.completions.create(
        model="ep-20241101151030-lfwks",
        messages = [
            {"role": "system", "content": "你是一个回答评估专家，给定两个字符串prediction和reference，你需要给prediction和reference之间的相似程度打分，分数为0-100之间的整数，只准给出一个阿拉伯数字，不准输出任何其他额外内容，尽可能在0-100之间的区分度比较大，不要集中在某一个区间"},
            {"role": "user", "content": f"prediction:{prediction.lower()}, reference: {reference.lower()}"},
        ],
    )
    score = (int)(completion.choices[0].message.content)
    print(f"score:{score}")
    print(f"")
    
    return {"key": "custom_score_match", "score": score}

evalutorType = "custom_score_match"
# # Evaluator
# qa_evalulator = [
#     LangChainStringEvaluator(
#         evalutorType,    # 具体种类，可以点一下LangChainStringEvaluator类，进去后点一下StringEvaluator类，搜索EvaluatorType，有完整的
#         prepare_data=lambda run, example: {
#             "prediction": run.outputs["answer"],
#             "reference": example.outputs["answer"],
#             "input": example.inputs["prompt"],
#         },
#     )
# ]


# example: 
dataset_name = "t-rag-new"
experiment_results = evaluate(
    predict_rag_answer,
    data=dataset_name,
    # evaluators=qa_evalulator,
    evaluators=[custom_score_match],
    experiment_prefix=f"{dataset_name}-{evalutorType}-tree-num-{tree_num_max}-method-{search_method}",
    metadata={"variant": "t-rag"},
)