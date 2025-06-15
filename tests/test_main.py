import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "main", Path(__file__).resolve().parents[1] / "main.py"
)
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)

class DummyDoc:
    def __init__(self, metadata):
        self.metadata = metadata


def test_get_links_with_summaries_includes_general(monkeypatch):
    query_doc = DummyDoc({'source': 'doc1.pdf', 'summary': 'doc1 sum', 'tags': []})
    general_doc = DummyDoc({'source': 'general.txt', 'summary': 'gen sum', 'tags': ['general']})

    class DummyIndex:
        def __init__(self):
            self.docstore = type('ds', (), {'_dict': {'q': query_doc, 'g': general_doc}})()

        def similarity_search_with_score(self, query, k=15):
            return [(query_doc, 0.1)]

    monkeypatch.setattr(main, 'VECTOR_INDEX', DummyIndex())
    monkeypatch.setattr(main, 'AZURE_BLOB_BASE_URL', 'https://files/')

    links = main.get_links_with_summaries('query')
    assert {'name': 'doc1.pdf', 'url': 'https://files/doc1.pdf', 'summary': 'doc1 sum'} in links
    assert {'name': 'general.txt', 'url': 'https://files/general.txt', 'summary': 'gen sum'} in links
