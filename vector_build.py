import os
import fitz  # PyMuPDF
import docx
import pptx
from azure.storage.blob import BlobServiceClient
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv

# ── Load environment variables ──
load_dotenv()

# ── Azure Blob Storage Settings ──
connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
container_name = "resources"
blob_service_client = BlobServiceClient.from_connection_string(
    connection_string)
container_client = blob_service_client.get_container_client(container_name)

# ── Download directory ──
download_dir = "./downloads"
os.makedirs(download_dir, exist_ok=True)

# ── LLM for summaries ──
llm = ChatOpenAI(model="gpt-3.5-turbo")

# ── Document gathering ──
documents = []

for blob in container_client.list_blobs():
    blob_name = blob.name
    download_path = os.path.join(download_dir, blob_name)

    # Create nested dirs if needed
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    with open(download_path, "wb") as f:
        f.write(container_client.download_blob(blob).readall())
    print(f"✅ Downloaded: {blob_name}")

    ext = blob_name.lower().split(".")[-1]
    try:
        if ext == "pdf":
            with fitz.open(download_path) as doc:
                text = "\n".join([page.get_text() for page in doc])
        elif ext == "docx":
            text = "\n".join(
                [p.text for p in docx.Document(download_path).paragraphs])
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
            print(f"⚠️ Unsupported file format: {blob_name}")
            continue

        # Generate short summary (2–3 sentences)
        prompt = f"""
Summarise the following document in 2–3 concise sentences. Focus on its key purpose and intended use for academic staff embedding employability skills.

Content:
{text[:3000]}  # Safety limit on input length

Summary:
"""
        summary = llm.invoke(prompt).content.strip()

        documents.append(
            Document(page_content=text,
                     metadata={
                         "source": blob_name,
                         "summary": summary
                     }))
        print(f"✅ Processed: {blob_name}")
    except Exception as e:
        print(f"❌ Error processing {blob_name}: {e}")

# ── Split & embed ──
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                               chunk_overlap=100)
split_docs = text_splitter.split_documents(documents)

embedding = OpenAIEmbeddings()
db = FAISS.from_documents(split_docs, embedding)
db.save_local("faiss_index")
print("✅ FAISS index built and saved")
