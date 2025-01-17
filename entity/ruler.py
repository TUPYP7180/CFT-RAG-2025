import spacy
import csv
import random
from spacy.pipeline import EntityRuler
from trag_tree import hash


def enhance_spacy(entities):
    nlp = spacy.load("zh_core_web_sm")

    ruler = nlp.add_pipe("entity_ruler", before="ner")

    patterns = []

    for entity in entities:
        pattern = []
        words = list(entity.lower().strip().split())
        for word in words:
            pattern.append({"LOWER": word})

        patterns.append({"label": "EXTRA", "pattern": pattern})

    ruler.add_patterns(patterns)

    return nlp


def search_entity_info(tree, nlp, search, method=1):

    search_context = []

    if method == 0: 
        return search_context
    
    search = search.lower().strip()

    doc = nlp(search)
    for ent in doc.ents:
        if ent.label_ == 'EXTRA':
            if method == 1:
                result = tree.bfs_search(ent.text)
                if result is not None:
                    search_context.append(result)
            elif method == 2:
                result = tree.bfs_search2(ent.text)
                if result is not None:
                    search_context.append(result)
            # elif method == 3:
            #     search_context.append(tree.layer_search(ent.text))
            elif method == 5:
                result = tree.bfs_search3(ent.text)
                if result is not None:
                    search_context.append(result)
            elif method == 6:
                result = tree.bfs_search4(ent.text)
                if result is not None:
                    search_context.append(result)
            else:
                print("not supported method")
                return None

    return search_context


def search_entity_info_naive_hash(nlp, search):

    search_context = []
    search = search.lower().strip()

    doc = nlp(search)
    for ent in doc.ents:
        if ent.label_ == 'EXTRA' and ent.text in hash.node_hash:
            # print(f"search entity: {ent.text}")
            # print(hash.node_hash[ent.text])
            search_context += hash.node_hash[ent.text]

    random.shuffle(search_context)
    
    return search_context

def search_entity_info_cuckoofilter(nlp, search):

    search_context = []
    search = search.lower().strip()

    doc = nlp(search)
    for ent in doc.ents:
        if ent.label_ == 'EXTRA':
            find_ = hash.cuckoo_extract(ent.text)
            if find_ is not None:
                search_context += list(find_.split("。"))
    random.shuffle(search_context)
    search_context = "\n".join(search_context)
    return search_context
