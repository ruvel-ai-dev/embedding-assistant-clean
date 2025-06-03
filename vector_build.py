import os
import fitz  # PyMuPDF
import docx
import pptx
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Connect to Azure Blob Storage
connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
container_name = "resources"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Download all blobs from Azure storage
download_dir = "./downloads"
os.makedirs(download_dir, exist_ok=True)

documents = []
for blob in container_client.list_blobs():
    blob_name = blob.name
    download_path = os.path.join(download_dir, blob_name)
    with open(download_path, "wb") as f:
        blob_client = container_client.get_blob_client(blob)
        f.write(blob_client.download_blob().readall())
    print(f"✅ Downloaded: {blob_name}")

    ext = blob_name.lower().split(".")[-1]
    try:
        if ext == "pdf":
            with fitz.open(download_path) as doc:
                text = "\n".join([page.get_text() for page in doc])
        elif ext == "docx":
            text = "\n".join([p.text for p in docx.Document(download_path).paragraphs])
        elif ext == "pptx":
            prs = pptx.Presentation(download_path)
            text = "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        elif ext == "txt":
            with open(download_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            print(f"⚠️ Unsupported file format: {blob_name}")
            continue

        documents.append({"text": text, "source": blob_name})
        print(f"✅ Processed: {blob_name}")
    except Exception as e:
        print(f"❌ Error reading {blob_name}: {e}")

# Convert to LangChain documents
from langchain.schema import Document
docs = [Document(page_content=doc["text"], metadata={"source": doc["source"]}) for doc in documents]

# Split and embed
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_docs = text_splitter.split_documents(docs)

embedding = OpenAIEmbeddings()
db = FAISS.from_documents(split_docs, embedding)
db.save_local("faiss_index")
print("✅ FAISS index built and saved")

