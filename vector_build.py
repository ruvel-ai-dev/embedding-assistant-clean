import os
import json
from io import BytesIO
from azure.storage.blob import BlobServiceClient

import fitz  # PyMuPDF
import docx
from pptx import Presentation

from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

from dotenv import load_dotenv
load_dotenv()

# ── Connect to Azure Blob ──
connection_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = "resources"
blob_service = BlobServiceClient.from_connection_string(connection_str)
container_client = blob_service.get_container_client(container_name)

# ── Load and parse supported files ──
docs = []

for blob in container_client.list_blobs():
    filename = blob.name
    try:
        stream = container_client.get_blob_client(blob).download_blob().readall()
        text = ""

        if filename.endswith(".pdf"):
            with fitz.open(stream=BytesIO(stream), filetype="pdf") as pdf:
                for page in pdf:
                    text += page.get_text()

        elif filename.endswith(".docx"):
            doc = docx.Document(BytesIO(stream))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        elif filename.endswith(".pptx"):
            prs = Presentation(BytesIO(stream))
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"

        else:
            print(f"⚠️ Skipping unsupported file: {filename}")
            continue

        docs.append(Document(page_content=text, metadata={"source": filename}))
        print(f"✅ Processed: {filename}")

    except Exception as e:
        print(f"❌ Failed to process {filename} → {e}")

# ── Optionally include pathways.json ──
try:
    with open("pathways.json", "r", encoding="utf-8") as f:
        pathway_data = json.load(f)
    for entry in pathway_data:
        content = f"{entry['title']}\n{entry['description']}\n{entry['url']}"
        docs.append(Document(page_content=content, metadata={"source": "pathways.json"}))
    print("✅ Pathways added to document list")
except Exception as e:
    print(f"⚠️ Could not read pathways.json → {e}")

# ── Split and embed ──
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
split_docs = text_splitter.split_documents(docs)

embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(split_docs, embedding)

vectorstore.save_local("faiss_index")
print("✅ FAISS index built and saved")
