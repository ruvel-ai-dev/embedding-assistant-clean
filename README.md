# Embedding Assistant – Careers Resource Recommender (Prototype)

This is a working prototype of an AI-powered assistant designed to support academic staff at the University of Greenwich in embedding employability into the curriculum. It enables lecturers and tutors to access tailored careers resources and pathways based on their subject area, academic level, and module needs.

## Purpose

Academic staff often face challenges in identifying employability resources that align with their teaching content. This tool simplifies the process by providing intelligent recommendations based on a brief module description.

- Careers and Employability Advisors manage a centralised resource bank (Word documents, PDFs, presentations, and curated pathway links).
- Lecturers complete a short online form describing their module and context.
- The assistant returns curated guidance, resource links, and career pathways using AI and semantic search.

## Features

### 🔍 Intelligent Semantic Matching

- Uses FAISS vector stores and OpenAI embeddings to match user input with both documents and pathways based on semantic similarity, not just keywords.

### 📄 Downloadable Documents

- Relevant PDF, Word, and PowerPoint files are dynamically retrieved from Azure Blob Storage.
- Users can select individual or multiple documents to download as a single ZIP file for offline use or Moodle upload.
- Each document includes a GPT-generated summary for easier previewing.

### 🔗 Pathway Recommendations (Now Exportable)

- The assistant suggests semantically relevant employability pathways from a structured list (`pathways.json`), including:
  - Title
  - Description
  - Direct link
- Selected pathway links can now be exported as a downloadable `.txt` file inside the ZIP package alongside documents.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` file

```env
OPENAI_API_KEY=sk-...
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=...
```

### 3. Build the Vector Index

This downloads files from Azure Blob Storage and embeds their contents.

```bash
python vector_build.py
```

### 4. Build the Pathway Index

Run this whenever `pathways.json` is modified:

```bash
python build_pathway_index.py
```

## AI Persona

The assistant follows a professional persona tailored to the UK Higher Education context:

> "You are the Greenwich Employability Embedding Assistant, an employability adviser for the Employability & Apprenticeship Directorate at the University of Greenwich (UK). You support academic staff (lecturers, module leaders, tutors) in embedding employability skills and resources into the curriculum. You write in clear, concise British English, maintaining a professional tone."

## How It Works

1. Lecturer enters:
   - Subject area
   - Academic level (Foundation, Undergraduate, or Postgraduate)
   - Module title
   - Additional notes or context
2. Assistant responds with:
   - Custom-written guidance from the GPT model
   - Downloadable, matched documents (with summaries)
   - Relevant employability pathways (optional `.txt` export)

## Technologies Used

- **Backend:** Python, Flask
- **Frontend:** HTML, JavaScript, Bootstrap
- **AI:** OpenAI GPT-4 (via API), FAISS, LangChain
- **Storage:** Azure Blob Storage
- **Deployment:** Replit
- **Search:** Semantic similarity using OpenAI Embeddings

## Notes

- Academic staff do not upload resources themselves.
- File uploads and updates are centrally managed by the Employability Team.
- The interface avoids technical language and remains intuitive for non-technical users.

## Planned Enhancements

- Admin dashboard for authenticated resource uploads
- Integration with OneDrive or SharePoint for dynamic storage
- Secure login for staff
- Moodle-compatible export formatting
- Analytics and usage dashboard

## Author

This assistant was developed by **Ruvel AI Dev** in collaboration with the **University of Greenwich Careers and Employability Service**, to enhance the practical integration of employability within the curriculum across all subject areas.

