import json

try:
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
except ModuleNotFoundError as e:
    missing = str(e).split("'")[1]
    print(
        f"Required package '{missing}' is not installed.\n"
        "Run 'pip install -r requirements.txt' and try again."
    )
    raise SystemExit(1)

# Load pathway data
with open("pathways.json", "r", encoding="utf-8") as f:
    data = json.load(f)

texts = []
metadatas = []
for entry in data:
    text = f"{entry.get('title', '')}\n{entry.get('description', '')}"
    texts.append(text)
    metadatas.append({
        "title": entry.get("title", ""),
        "description": entry.get("description", ""),
        "url": entry.get("url", "")
    })

# Build and save FAISS index
embeddings = OpenAIEmbeddings()
index = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
index.save_local("pathways_index")
print(f"✅ Built pathways_index with {len(texts)} entries")
