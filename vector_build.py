import os
import fitz
import docx
from pptx import Presentation
from io import BytesIO
from azure.storage.blob import BlobServiceClient

from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# Connect to Azure Blob Storage
conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_service = BlobServiceClient.from_connection_string(conn_str)
container = blob_service.get_container_client("resources")

def extract_text_from_blob(blob_name):
    blob = container.get_blob_client(blob_name)
    stream = BytesIO(blob.download_blob().readall())

    if blob_name.endswith(".pdf"):
        text = ""
        with fitz.open(stream=stream, filetype="pdf") as pdf:
            for page in pdf:
                text += page.get_text()
        return text

    elif blob_name.endswith(".docx"):
        doc = docx.Document(stream)
        return "\n".join(p.text for p in doc.paragraphs)

    elif blob_name.endswith(".pptx"):
        prs = Presentation(stream)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    return ""

def build_vectorstore():
    documents = []
    for blob in container.list_blobs():
        text = extract_text_from_blob(blob.name)
        documents.append(text)

    print("✅ Read all files from Azure. Now chunking and embedding...")

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_chunks = splitter.create_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(all_chunks, embeddings)
    vectorstore.save_local("faiss_index")

    print("✅ Vector store built and saved as 'faiss_index'.")

if __name__ == "__main__":
    build_vectorstore()
