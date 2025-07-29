from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
from fs_generator import generate_fs_from_requirement
from docx_writer import create_docx
import io

app = FastAPI()

@app.post("/generate-fs/")
async def generate_fs(requirement: str = Form(...)):
    fs_text = generate_fs_from_requirement(requirement)
    docx_buffer = io.BytesIO()
    create_docx(fs_text, docx_buffer)
    docx_buffer.seek(0)
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=functional_spec.docx"}
    )