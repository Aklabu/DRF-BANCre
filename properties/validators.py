import os

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    'pdf', 'png', 'jpg', 'jpeg',
    'xlsx', 'xls', 'csv',
    'pptx', 'ppt',
    'docx', 'doc',
}


def validate_document_file(file):
    # Validate a single uploaded file against size and type constraints.
    # Check file size
    if file.size > MAX_FILE_SIZE_BYTES:
        size_mb = file.size / (1024 * 1024)
        return False, (
            f"'{file.name}' exceeds the maximum allowed size of {MAX_FILE_SIZE_MB}MB "
            f"(uploaded size: {size_mb:.2f}MB)."
        )

    # Check file extension
    ext = os.path.splitext(file.name)[1].lstrip('.').lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, (
            f"'{file.name}' has an unsupported file type (.{ext}). "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    return True, None


def validate_documents(files):
    # Validate a list of uploaded files and return valid files and error messages.
    valid_files = []
    errors = []

    for file in files:
        is_valid, error = validate_document_file(file)
        if is_valid:
            valid_files.append(file)
        else:
            errors.append(error)

    return valid_files, errors