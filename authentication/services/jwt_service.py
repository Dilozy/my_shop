import base64
import hmac
import hashlib
import os
import json
import uuid
from datetime import timedelta

from django.utils import timezone


class JWT:
    @staticmethod
    def base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    @staticmethod
    def create_access_token(user):
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"username": user.phone_number,
                   "email": user.email,
                   "sub": user.id,
                   "jti": str(uuid.uuid4()),
                   "exp": int((timezone.now() + timedelta(minutes=15)).timestamp())}
        
        header_b64 = JWT.base64url_encode(json.dumps(header).encode())
        payload_b64 = JWT.base64url_encode(json.dumps(payload).encode())
        signature = hmac.new(
            os.getenv("DJANGO_SECRET_KEY").encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = JWT.base64url_encode(signature)

        return "{}.{}.{}".format(header_b64, payload_b64, signature_b64)

    @staticmethod
    def decode_access_token(token):
        header_b64, payload_b64, signature_b64 = token.split(".")
        header_payload = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(
            os.getenv("DJANGO_SECRET_KEY").encode(),
            header_payload,
            hashlib.sha256
        ).digest()
        expected_sig_b64 = JWT.base64url_encode(expected_sig)

        payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode()
        payload = json.loads(payload_json)

        return signature_b64, expected_sig_b64, payload
        
