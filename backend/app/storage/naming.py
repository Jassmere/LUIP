from datetime import datetime
from pathlib import Path
from uuid import uuid4


def generate_filename(original_filename: str) -> str:
    """
    Generate an enterprise-grade unique filename.

    Example:
    20260721_154458_a8d73f91_Master Services Agreement.pdf
    """

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    unique_id = uuid4().hex[:8]

    extension = Path(original_filename).suffix

    name = Path(original_filename).stem

    safe_name = name.replace("/", "_").replace("\\", "_")

    return f"{timestamp}_{unique_id}_{safe_name}{extension}"