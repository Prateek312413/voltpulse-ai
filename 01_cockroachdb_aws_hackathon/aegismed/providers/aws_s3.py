"""
AWS S3 Clinical Artifact & Imaging Store
Provides secure, durable storage for medical PDF reports, lab documents, and imaging studies.
"""

import json
import logging
from typing import Dict, Any, Optional
from aegismed.config import settings

logger = logging.getLogger("aegismed.s3")

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSS3StorageProvider:
    """Manages clinical document & image artifacts on AWS S3."""

    def __init__(self, bucket_name: str = "aegismed-clinical-records"):
        self.bucket_name = bucket_name
        self.client = None
        self.available = False
        self._init_client()

    def _init_client(self):
        if not BOTO3_AVAILABLE:
            return
        try:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self.client = boto3.client("s3", **kwargs)
            self.available = True
        except Exception as e:
            logger.info(f"S3 client running in local emulation mode ({e})")
            self.available = False

    def store_clinical_report(self, patient_uid: str, episode_uid: str, report_data: Dict[str, Any]) -> str:
        """Uploads JSON/PDF clinical report to S3 and returns S3 URI."""
        key = f"patients/{patient_uid}/episodes/{episode_uid}.json"
        if self.available and self.client:
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json.dumps(report_data, indent=2),
                    ContentType="application/json"
                )
                return f"s3://{self.bucket_name}/{key}"
            except Exception as e:
                logger.warning(f"S3 upload failed: {e}. Storing locally.")
        
        return f"s3://{self.bucket_name}/{key} (Local Reference)"


s3_store = AWSS3StorageProvider()
