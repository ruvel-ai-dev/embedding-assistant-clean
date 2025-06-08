import os
import fitz  # PyMuPDF
import docx
import pptx
import json
import hashlib
import time
import traceback
from azure.storage.blob import BlobServiceClient
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv

# ── Load environment variables ──
load_dotenv()

# ── Azure Storage Setup ──
connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
container_name = "resources"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# ── Temporary Download Folder ──
download_dir = "./downloads"
os.makedirs(download_dir, exist_ok=True)

# ── Hash Tracking File ──
hash_file_path = "document_hashes.json"
if os.path.exists(hash_file_path):
    with open(hash_file_path, "r") as f:
        stored_hashes = json.load(f)
else:
    stored_hashes = {}

# ── Load or Create FAISS Index ──
embedding = OpenAIEmbeddings()
index_path = "faiss_index"
if os.path.exists(index_path):
    db = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True)
    print("📂 Existing FAISS index loaded")
else:
    db = None
    print("📁 No existing FAISS index found. A new one will be created.")

# ── GPT-4 LLM Setup ──
llm = ChatOpenAI(model="gpt-4-1106-preview")
documents = []
DRY_RUN = False  # ✅ Set True if you want to test without saving the index

# ── Utility: Compute file hash ──
def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# ── Retry Wrapper for LLM Calls ──
def try_invoke(prompt, retries=3):
    for attempt in range(retries):
        try:
            return llm.invoke(prompt).content.strip()
        except Exception as e:
            print(f"⚠️ Retry {attempt+1} failed: {e}")
            time.sleep(2)
    raise Exception("Max retries exceeded.")

# ── Process Files ──
for blob in container_client.list_blobs():
    blob_name = blob.name
    download_path = os.path.join(download_dir, blob_name)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    try:
        with open(download_path, "wb") as f:
            f.write(container_client.download_blob(blob).readall())
        print(f"✅ Downloaded: {blob_name}")

        current_hash = compute_md5(download_path)
        if blob_name in stored_hashes and stored_hashes[blob_name] == current_hash:
            print(f"⏭️ Skipped (unchanged): {blob_name}")
            continue

        ext = blob_name.lower().split(".")[-1]
        if ext == "pdf":
            with fitz.open(download_path) as doc:
                text = "\n".join([page.get_text() for page in doc])
        elif ext == "docx":
            text = "\n".join([p.text for p in docx.Document(download_path).paragraphs])
        elif ext == "pptx":
            prs = pptx.Presentation(download_path)
            text = "\n".join([
                shape.text for slide in prs.slides for shape in slide.shapes
                if hasattr(shape, "text")
            ])
        elif ext == "txt":
            with open(download_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            print(f"⚠️ Unsupported format: {blob_name}")
            continue

        safe_text = text[:12000]  # truncate input safely

        # Generate summary
        summary_prompt = f"""Summarise this document in 2–3 concise sentences suitable for academic staff. Highlight employability-related content, if present:\n\n{safe_text}"""
        summary = try_invoke(summary_prompt)

        # Generate tags
        tag_prompt = f"""List 5 comma-separated, lowercase tags describing the main themes of this document (e.g. cv, interviews, placements):\n\n{safe_text}"""
        tag_response = try_invoke(tag_prompt)
        tags = [t.strip() for t in tag_response.split(",") if t.strip()]

        # Validate outputs
        if not summary or not isinstance(summary, str):
            print(f"⚠️ Skipped {blob_name} due to empty summary")
            continue
        if not tags or not isinstance(tags, list):
            print(f"⚠️ Skipped {blob_name} due to empty tags")
            continue

        # Add document
        doc = Document(
            page_content=text,
            metadata={
                "source": blob_name,
                "summary": summary,
                "tags": tags
            }
        )
        documents.append(doc)
        stored_hashes[blob_name] = current_hash
        print(f"🆕 Processed & tagged: {blob_name}")

    except Exception as e:
        print(f"❌ Error processing {blob_name}:\n{traceback.format_exc()}")

# ── Split & Add to FAISS ──
if documents:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)
    if db:
        db.add_documents(split_docs)
    else:
        db = FAISS.from_documents(split_docs, embedding)
    if not DRY_RUN:
        db.save_local(index_path)
        print("✅ FAISS vector index updated")
    else:
        print("🧪 Dry run: FAISS index not saved")
else:
    print("📭 No new or changed documents to embed")

# ── Save updated hashes ──
with open(hash_file_path, "w") as f:
    json.dump(stored_hashes, f, indent=2)
print("📝 Document hashes updated")

