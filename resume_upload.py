import os
from werkzeug.utils import secure_filename
from datetime import datetime
from config import RESUME_FOLDER, allowed_resume_file

def save_resume(file, user_id: int, job_id: int) -> tuple[str | None, str | None]:
    """
    Save the uploaded resume file with a safe, unique name.

    Returns:
        (filename, error_message)
        - filename (str): saved resume filename (not full path)
        - error_message (str): None if success, else reason for failure
    """
    if not file or file.filename == "":
        return None, "No file selected"

    # Validate file extension
    if not allowed_resume_file(file.filename):
        return None, "Invalid file type"

    # Make filename safe
    filename = secure_filename(file.filename)

    # Add timestamp, user_id and job_id for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"user{user_id}_job{job_id}_{timestamp}_{filename}"

    # Save file in resume upload folder
    filepath = os.path.join(RESUME_FOLDER, unique_filename)
    try:
        file.save(filepath)
    except Exception as e:
        return None, f"Error saving file: {e}"

    return unique_filename, None
