from app.schemas import documents as schemas_documents

MAX_FILE_SIZE = 1024 * 1024 * 10

FILE_EXTENSION: tuple = (".pdf", ".md")

DOCUMENT_WEIGHT: dict[int, int] = {
    schemas_documents.DocumentType.STANDARD.value: 0.3,
    schemas_documents.DocumentType.CASE.value: 0.4,
    schemas_documents.DocumentType.SOP.value: 0.3,
}
