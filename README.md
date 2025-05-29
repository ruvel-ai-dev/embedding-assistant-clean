# Embedding Assistant – Careers Resource Recommender (Prototype)

This is a working prototype AI assistant built to help university lecturers access careers materials tailored to their **module, academic level, and subject**.

## Purpose
Lecturers often struggle to find the right employability resources for their course. This assistant streamlines that process.

- Advisors (not lecturers) maintain the central resource bank (PDFs, Word, PPTs, links).
- Lecturers submit queries via a simple form.
- The assistant recommends downloadable resources instantly, based on subject, level, and module content.

## Powered By
- Python (Flask) – for backend
- HTML/CSS/JavaScript – for frontend
- OpenAI GPT API – for natural language understanding
- Hosted on Replit
- Resources stored in `static/` folder

## Current Demo Resources
These are example materials embedded for demonstration:

- [CV Template (Word)](/static/cv-template.pptx)
- [Cover Letter Guide (Word)](/static/cover-letter.docx)
- [Employability Checklist (PDF)](/static/checklist.pdf)

> All resources live in the `static/` directory and are hard-linked from within responses.

## How It Works
1. User fills in form:
   - Subject Area
   - Academic Level (Foundation, Undergraduate, Postgraduate)
   - Module Title
   - Additional Notes

2. Assistant sends prompt to GPT API

3. GPT returns relevant guidance + links to resources (pre-uploaded in `static/`)

## Notes
- Lecturers **do not upload** anything.
- Advisors update the `static/` folder or future OneDrive/Moodle integration.

## Future Roadmap
- OneDrive integration to host live documents (for internal staff use).
- Admin interface for advisors to add/remove resource links.
- Streamlit version for advanced visualisation.
- Embedding-based semantic search instead of keyword-based matching.

## 👨‍💼 Author
Developed by [Ruvel AI Dev](https://github.com/ruvel-ai-dev) for University of Greenwich careers support integration.

