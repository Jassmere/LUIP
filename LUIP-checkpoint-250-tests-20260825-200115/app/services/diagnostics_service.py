import os
from datetime import datetime


class DiagnosticsService:
    """
    LUIP Diagnostics Engine (LDE)

    Performs automatic health checks across the platform.
    """

    @staticmethod
    def run():

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "Healthy",
            "checks": []
        }

        # -----------------------------
        # Storage Folder Check
        # -----------------------------

        storage_path = "storage"

        if os.path.exists(storage_path):

            report["checks"].append({
                "component": "Storage",
                "status": "OK",
                "message": "Storage directory found."
            })

        else:

            report["overall_status"] = "Warning"

            report["checks"].append({
                "component": "Storage",
                "status": "WARNING",
                "message": "Storage directory missing."
            })

        # -----------------------------
        # Documents Folder Check
        # -----------------------------

        documents_path = os.path.join(
            storage_path,
            "contracts"
        )

        if os.path.exists(documents_path):

            report["checks"].append({
                "component": "Contracts Storage",
                "status": "OK",
                "message": "Contracts folder exists."
            })

        else:

            report["overall_status"] = "Warning"

            report["checks"].append({
                "component": "Contracts Storage",
                "status": "WARNING",
                "message": "Contracts folder missing."
            })

        return report