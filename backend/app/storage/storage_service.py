from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

from app.storage.checksum import calculate_checksum
from app.storage.naming import generate_filename
from app.storage.storage import get_contract_storage_directory


class StorageService:
    """
    Enterprise storage service.

    Responsible ONLY for filesystem operations.

    It does NOT know anything about SQLAlchemy,
    FastAPI routers or business rules.
    """

    @staticmethod
    async def save_file(
        upload_file: UploadFile,
    ) -> Tuple[str, str, int, str]:

        storage_directory = get_contract_storage_directory()

        stored_filename = generate_filename(
            upload_file.filename
        )

        destination = (
            storage_directory /
            stored_filename
        )

        file_bytes = await upload_file.read()

        with open(destination, "wb") as buffer:
            buffer.write(file_bytes)

        checksum = calculate_checksum(destination)

        return (
            stored_filename,
            str(destination),
            len(file_bytes),
            checksum,
        )