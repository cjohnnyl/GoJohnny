from fastapi import Header, HTTPException
from app.core.config import VALID_API_KEYS


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="API key inválida ou ausente")
