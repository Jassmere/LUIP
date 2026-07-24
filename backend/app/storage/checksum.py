import hashlib
from pathlib import Path


def calculate_checksum(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(8192)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def calculate_checksum_bytes(file_bytes: bytes) -> str:
    """
    Calculate SHA-256 directly from bytes.
    Useful before writing the file to disk.
    """

    return hashlib.sha256(file_bytes).hexdigest()