from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# MockAuth: a static token so the frontend can connect without a real login flow.
MOCK_TOKEN = "mock-token-wmd-mvp"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/mock-login", response_model=TokenResponse)
def mock_login():
    return TokenResponse(access_token=MOCK_TOKEN)
