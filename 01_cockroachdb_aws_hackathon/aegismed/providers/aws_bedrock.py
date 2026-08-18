"""
AWS Bedrock Provider for AegisMed
Connects to Amazon Bedrock for Foundation Models (Claude 3.5 Sonnet / Llama 3)
and Amazon Titan Text Embeddings v2.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from aegismed.config import settings

logger = logging.getLogger("aegismed.bedrock")

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSBedrockProvider:
    """Enterprise client for AWS Bedrock AI and Vector Embedding services."""

    def __init__(self):
        self.client = None
        self.available = False
        self._initialize_client()

    def _initialize_client(self):
        if not BOTO3_AVAILABLE:
            logger.info("boto3 not installed or disabled.")
            return

        try:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
            
            self.client = boto3.client("bedrock-runtime", **kwargs)
            # Lightweight verification
            self.available = True
            logger.info(f"Initialized AWS Bedrock Runtime Client in region {settings.AWS_REGION}")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Bedrock credentials not detected or invalid ({e}). Operating in Local Hybrid Mode.")
            self.available = False
        except Exception as e:
            logger.warning(f"Error initializing AWS Bedrock: {e}")
            self.available = False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generates high-dimensional vector embedding using Amazon Titan Embeddings v2."""
        if not self.available or not self.client:
            return None

        try:
            body = json.dumps({
                "inputText": text,
                "dimensions": settings.VECTOR_DIMENSION,
                "normalize": True
            })
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding")
            return embedding
        except Exception as e:
            if "credentials" in str(e).lower() or "security token" in str(e).lower():
                self.available = False
                logger.info("AWS Bedrock credentials not detected. Operating seamlessly with local semantic engine.")
            else:
                logger.error(f"AWS Bedrock Embedding generation failed: {e}")
            return None

    def invoke_claude(self, prompt: str, system_prompt: str = "", max_tokens: int = 2048, temperature: float = 0.1) -> Optional[str]:
        """Invokes Anthropic Claude 3.5 Sonnet on AWS Bedrock."""
        if not self.available or not self.client:
            return None

        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_LLM_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            response_body = json.loads(response["body"].read())
            content = response_body.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return None
        except Exception as e:
            logger.error(f"AWS Bedrock Claude invocation failed: {e}")
            return None
