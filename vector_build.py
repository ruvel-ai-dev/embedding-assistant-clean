import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RESOURCE_DIR = "resources"
client = OpenAI(api_key=OPENAI_API_KEY)


def get_all_files(folder):
    return [
        os.path.join(folder, f) for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    ]


def generate_summary(text):
    prompt = f"Summarise this file in 1–2 sentences:\n\n{text[:1000]}"
    resp = client.chat.completions.create(model="gpt-4-1106-preview",
                                          messages=[{
                                              "role": "user",
                                              "content": prompt
                                          }],
                                          max_tokens=100)
    return resp.choices[0].message.content.strip()


def detect_tags(fname, summary):
    tags = []
    lowered = (fname + " " + summary).lower()
    if any(word in lowered for word in
           ["cv", "cover", "checklist", "template", "main", "general"]):
        tags.append("general")
    return tags


def main():
    all_files = get_all_files(RESOURCE_DIR)
    docs_with_metadata = []

    for file_path in all_files:
        loader = UnstructuredFileLoader(file_path)
        docs = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000,
                                              chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        for doc in splits:
            summary = generate_summary(doc.page_content)
            fname = os.path.basename(file_path)
            tags = detect_tags(fname, summary)

            doc.metadata["source"] = fname
            doc.metadata["summary"] = summary
            doc.metadata["tags"] = tags
            docs_with_metadata.append(doc)

    print("✅ All documents processed. Now building FAISS index...")
    db = FAISS.from_documents(docs_with_metadata, OpenAIEmbeddings())
    db.save_local("faiss_index")
    print("✅ faiss_index saved.")


if __name__ == "__main__":
    main()
