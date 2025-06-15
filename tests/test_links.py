import types
import sys
import importlib
import os

# Utility to stub required modules for importing main

def import_main():
    modules = {}

    # flask stub
    flask = types.ModuleType('flask')
    class DummyFlask:
        def __init__(self, *a, **kw):
            self.static_folder = kw.get("static_folder", "")
        def route(self, *a, **kw):
            def decorator(f):
                return f
            return decorator
        def send_static_file(self, *a, **kw):
            pass
    flask.Flask = DummyFlask
    flask.request = types.SimpleNamespace(get_json=lambda: {})
    flask.jsonify = lambda *a, **kw: None
    flask.send_from_directory = lambda *a, **kw: None
    flask.send_file = lambda *a, **kw: None
    modules['flask'] = flask

    # dotenv stub
    dotenv = types.ModuleType('dotenv')
    dotenv.load_dotenv = lambda *a, **kw: None
    modules['dotenv'] = dotenv

    # openai stub
    openai = types.ModuleType('openai')
    openai.OpenAI = lambda *a, **kw: None
    modules['openai'] = openai

    # azure blob stub
    azure = types.ModuleType('azure')
    storage = types.ModuleType('azure.storage')
    blob = types.ModuleType('azure.storage.blob')
    blob.BlobServiceClient = object
    storage.blob = blob
    azure.storage = storage
    modules['azure'] = azure
    modules['azure.storage'] = storage
    modules['azure.storage.blob'] = blob

    # langchain stubs
    lc_comm = types.ModuleType('langchain_community')
    faiss = types.ModuleType('langchain_community.vectorstores')
    faiss.FAISS = object
    emb = types.ModuleType('langchain_community.embeddings')
    emb.OpenAIEmbeddings = object
    modules['langchain_community'] = lc_comm
    modules['langchain_community.vectorstores'] = faiss
    modules['langchain_community.embeddings'] = emb

    chains = types.ModuleType('langchain.chains')
    chains.RetrievalQA = object
    modules['langchain.chains'] = chains

    lco = types.ModuleType('langchain_openai')
    lco.ChatOpenAI = object
    modules['langchain_openai'] = lco

    for name, mod in modules.items():
        sys.modules.setdefault(name, mod)

    # Ensure project root on path
    root_dir = os.path.dirname(os.path.dirname(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    return importlib.import_module('main')


class DummyDoc:
    def __init__(self, name, summary, tags=None):
        self.metadata = {
            'source': name,
            'summary': summary,
            'tags': tags or []
        }


class DummyIndex:
    def __init__(self, query_docs, general_docs):
        # query_docs: list of (name, score, tags)
        self._query_docs = [
            (DummyDoc(n, f'sum-{n}', t), s) for n, s, t in query_docs
        ]
        self.docstore = type('ds', (), {'_dict': {}})()
        i = 0
        for doc, _ in self._query_docs:
            self.docstore._dict[f'q{i}'] = doc
            i += 1
        for name in general_docs:
            self.docstore._dict[f'g{i}'] = DummyDoc(name, f'sum-{name}', ['general'])
            i += 1

    def similarity_search_with_score(self, query, k=15):
        return self._query_docs[:k]


def test_general_docs_added_when_missing():
    main = import_main()
    main.AZURE_BLOB_BASE_URL = "http://blob/"
    main.VECTOR_INDEX = DummyIndex(
        query_docs=[('doc1.pdf', 0.1, []), ('doc2.pdf', 0.2, [])],
        general_docs=['gen1.pdf', 'gen2.pdf']
    )
    res = main.get_links_with_summaries('q', top_k=2)
    names = [r['name'] for r in res]
    assert names[:2] == ['doc1.pdf', 'doc2.pdf']
    assert 'gen1.pdf' in names and 'gen2.pdf' in names


def test_sorted_by_score():
    main = import_main()
    main.AZURE_BLOB_BASE_URL = "http://blob/"
    main.VECTOR_INDEX = DummyIndex(
        query_docs=[('docB.pdf', 0.2, []), ('docA.pdf', 0.1, []), ('docC.pdf', 0.15, [])],
        general_docs=['gen.pdf']
    )
    res = main.get_links_with_summaries('q', top_k=3)
    names = [r['name'] for r in res]
    assert names[:3] == ['docA.pdf', 'docC.pdf', 'docB.pdf']
    assert names[-1] == 'gen.pdf'


def test_keyword_boost_reranks():
    main = import_main()
    main.AZURE_BLOB_BASE_URL = "http://blob/"
    main.VECTOR_INDEX = DummyIndex(
        query_docs=[('catguide.pdf', 0.2, []), ('other.pdf', 0.1, [])],
        general_docs=[]
    )
    res = main.get_links_with_summaries('cat', top_k=2)
    names = [r['name'] for r in res]
    assert names[0] == 'catguide.pdf'


