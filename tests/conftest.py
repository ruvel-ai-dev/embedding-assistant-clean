import sys, types

# Stub flask
flask_mod = types.ModuleType('flask')
class DummyFlask:
    def __init__(self, *args, **kwargs):
        pass
    def route(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
flask_mod.Flask = DummyFlask
flask_mod.request = None
flask_mod.jsonify = lambda *a, **k: {}
flask_mod.send_from_directory = lambda *a, **k: None
flask_mod.send_file = lambda *a, **k: None
sys.modules.setdefault('flask', flask_mod)

# Stub openai
openai_mod = types.ModuleType('openai')
class DummyOpenAI:
    def __init__(self, *a, **k):
        pass
openai_mod.OpenAI = DummyOpenAI
sys.modules.setdefault('openai', openai_mod)

# Stub dotenv
dotenv_mod = types.ModuleType('dotenv')
dotenv_mod.load_dotenv = lambda *a, **k: None
sys.modules.setdefault('dotenv', dotenv_mod)

# Stub azure blob
azure_mod = types.ModuleType('azure')
azure_storage_mod = types.ModuleType('azure.storage')
azure_blob_mod = types.ModuleType('azure.storage.blob')
class DummyBlobServiceClient:
    @classmethod
    def from_connection_string(cls, *a, **k):
        return cls()
azure_blob_mod.BlobServiceClient = DummyBlobServiceClient
azure_storage_mod.blob = azure_blob_mod
azure_mod.storage = azure_storage_mod
sys.modules.setdefault('azure', azure_mod)
sys.modules.setdefault('azure.storage', azure_storage_mod)
sys.modules.setdefault('azure.storage.blob', azure_blob_mod)

# Stub docx/pptx/PyPDF2
Docx = types.ModuleType('docx')
class DummyDocxDocument:
    def __init__(self, *a, **k):
        self.paragraphs = []
Docx.Document = DummyDocxDocument
sys.modules.setdefault('docx', Docx)

pptx_mod = types.ModuleType('pptx')
class DummyPresentation:
    def __init__(self, *a, **k):
        self.slides = []
pptx_mod.Presentation = DummyPresentation
sys.modules.setdefault('pptx', pptx_mod)

pypdf_mod = types.ModuleType('PyPDF2')
class DummyPdfReader:
    def __init__(self, *a, **k):
        self.pages = []
pypdf_mod.PdfReader = DummyPdfReader
sys.modules.setdefault('PyPDF2', pypdf_mod)

# Stub langchain pieces used at import
lc_vs_mod = types.ModuleType('langchain_community.vectorstores')
class DummyFAISS:
    @staticmethod
    def load_local(*a, **k):
        return DummyFAISS()
    def as_retriever(self):
        return self
    def similarity_search(self, *a, **k):
        return []
lc_vs_mod.FAISS = DummyFAISS
sys.modules.setdefault('langchain_community.vectorstores', lc_vs_mod)

lc_emb_mod = types.ModuleType('langchain_community.embeddings')
class DummyEmbeddings:
    pass
lc_emb_mod.OpenAIEmbeddings = DummyEmbeddings
sys.modules.setdefault('langchain_community.embeddings', lc_emb_mod)

lc_openai_mod = types.ModuleType('langchain_openai')
class DummyChatOpenAI:
    def __init__(self, *a, **k):
        pass
    def invoke(self, prompt):
        class Res:
            content = ''
        return Res()
class DummyOpenAIEmbeddings:
    pass
lc_openai_mod.ChatOpenAI = DummyChatOpenAI
lc_openai_mod.OpenAIEmbeddings = DummyOpenAIEmbeddings
sys.modules.setdefault('langchain_openai', lc_openai_mod)

lc_ts_mod = types.ModuleType('langchain.text_splitter')
class DummySplitter:
    def __init__(self, *a, **k):
        pass
    def split_text(self, text):
        return [text]
lc_ts_mod.RecursiveCharacterTextSplitter = DummySplitter
sys.modules.setdefault('langchain.text_splitter', lc_ts_mod)

lc_schema_mod = types.ModuleType('langchain.schema')
class DummyDocument:
    def __init__(self, page_content=None, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}
lc_schema_mod.Document = DummyDocument
sys.modules.setdefault('langchain.schema', lc_schema_mod)

lc_chains_mod = types.ModuleType('langchain.chains')
class DummyRetrievalQA:
    @classmethod
    def from_chain_type(cls, llm=None, retriever=None):
        class Chain:
            def run(self, query):
                return ''
        return Chain()
lc_chains_mod.RetrievalQA = DummyRetrievalQA
sys.modules.setdefault('langchain.chains', lc_chains_mod)
