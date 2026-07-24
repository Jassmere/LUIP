from datetime import datetime
from pathlib import Path

#
# Project root inside Docker:
# /app
#
PROJECT_ROOT = Path(__file__).resolve().parents[2]

#
# Physical storage directory:
# /app/storage
#
BASE_STORAGE = PROJECT_ROOT / "storage"


def get_contract_storage_directory() -> Path:
    """
    Returns the contract storage directory.

    Example:

        /app/storage/contracts/2026/07
    """

    today = datetime.utcnow()

    directory = (
        BASE_STORAGE
        / "contracts"
        / today.strftime("%Y")
        / today.strftime("%m")
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory