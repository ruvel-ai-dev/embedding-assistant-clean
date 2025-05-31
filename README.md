# Embedding Assistant – Careers Resource Recommender (Prototype)

This is a working prototype of an AI-powered assistant developed to support academic staff at the University of Greenwich in embedding employability into their teaching. It enables lecturers and tutors to quickly access relevant careers resources tailored to their subject, module, and academic level.

## Purpose

Academic staff often find it difficult to identify suitable employability resources that align with their curriculum. This tool simplifies the process by offering tailored recommendations based on brief module descriptions.

- Careers and Employability Advisors maintain the central resource bank (PDFs, Word documents, presentations, and links).
- Lecturers complete a short form describing their module.
- The assistant returns relevant resources and guidance instantly using an AI model with embedded institutional knowledge.

## AI Persona

The assistant is configured with the following persona:

"You are the Greenwich Employability Embedding Assistant, an employability adviser for the Employability & Apprenticeship Directorate at the University of Greenwich (UK) with extensive experience. You support academic staff (lecturers, module leaders, tutors) in embedding employability skills and resources into the curriculum. You write using British English, in a concise, professional tone, avoiding technical implementation terms such as JSON or code."

## Features

### Downloadable Resources

The assistant matches keywords in user prompts to static downloadable documents. These include:

- CV Template (PowerPoint)
- Cover Letter Guide (Word)
- Employability Checklist (PDF)

All documents are stored in the `static/` directory and hard-linked in responses.

### Pathway Matching

The assistant also recommends relevant employability pathways based on subject-specific and skill-related keywords. Pathways are preloaded from a `pathways.json` file and include:

- A title
- A description
- A direct link

These may cover areas such as sector-specific CVs, employer project briefs, and skills reflection activities.

## How It Works

1. The user enters the following information:
   - Subject Area
   - Academic Level (Foundation, Undergraduate, or Postgraduate)
   - Module Title
   - Additional Notes

2. This input is sent to the OpenAI GPT model, along with the predefined persona.

3. The model generates:
   - Written guidance appropriate to the context
   - A list of matching downloadable documents
   - A list of relevant pathways

These are presented in three sections on the web page.

## Technologies Used

- Python (Flask) – for backend API
- HTML, CSS, JavaScript – for frontend interface
- OpenAI GPT API – for language generation
- Hosted on Replit
- Resources stored locally in `static/`

## Notes

- Lecturers do not upload materials.
- Resource updates are managed by Careers and Employability staff.
- The interface avoids technical explanations and presents information in a clear, academic-friendly format.

## Planned Enhancements

- Integration with OneDrive or SharePoint for dynamic file management
- Admin dashboard for resource uploads
- Streamlit-based version with filters and analytics
- Embedding-based semantic search for more accurate recommendations
- Login authentication for staff-only access

## Author

This prototype was developed by Ruvel AI Dev in collaboration with the University of Greenwich Careers and Employability Service, to improve the embedding of employability across the curriculum.


