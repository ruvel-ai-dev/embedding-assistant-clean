from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load the FAISS index
vectorstore = FAISS.load_local("faiss_index", OpenAIEmbeddings(), allow_dangerous_deserialization=True)

# Inspect the documents in the index
docs = vectorstore.docstore._dict

print("\n📂 Documents in FAISS Index:\n")
for i, (doc_id, doc) in enumerate(docs.items()):
    print(f"{i + 1}. {doc.metadata.get('source', 'Unknown source')}")
