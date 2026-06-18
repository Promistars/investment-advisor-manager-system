from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    username: str


class MessageResponse(BaseModel):
    message: str
    ok: bool = True
