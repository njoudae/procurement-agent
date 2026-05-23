from fastapi import APIRouter, Request, Response

from app.security import clear_admin_session, create_dev_admin_session, require_admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login")
def dev_login(response: Response, request: Request) -> dict[str, str]:
    return create_dev_admin_session(response, request)


@router.get("/me")
def me(request: Request) -> dict[str, str]:
    require_admin(request)
    return {"role": "admin"}


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    return clear_admin_session(response)
