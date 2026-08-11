from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.auth import supabase
from app.models import SignupRequest, LoginRequest

router = APIRouter()


@router.post("/auth/signup", status_code=201, summary="Create a new user account")
def signup(payload: SignupRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    try:
        result = supabase.auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = result.user
    return {"id": user.id, "email": user.email, "created_at": user.created_at}


@router.post("/auth/login", summary="Authenticate and return a JWT")
def login(payload: LoginRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    if result.session is None:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "token_type": "bearer",
    }

def _extract_token(authorization: Optional[str]) -> str:
    """Missing, malformed, or empty -> 401. Not verified yet (Stage 3)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")
    return token


# ... keep signup() and login() from Stage 1 unchanged, then add:

@router.get("/public/info", summary="Public, open data -- no auth required")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@router.get("/protected/profile", summary="Read the logged-in user's private profile")
def profile(authorization: Optional[str] = Header(default=None)):
    token = _extract_token(authorization)
    return {"message": "Token received (not yet verified)", "token_preview": token[:12] + "..."}