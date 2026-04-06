# app/core/exceptions.py

from fastapi import HTTPException

class BusinessException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(BusinessException):
    def __init__(self, resource: str):
        super().__init__(detail=f"{resource} non trouvé", status_code=404)

class UnauthorizedException(BusinessException):
    def __init__(self):
        super().__init__(detail="Non authentifié", status_code=401)

class ForbiddenException(BusinessException):
    def __init__(self, detail: str = "Accès interdit"):
        super().__init__(detail=detail, status_code=403)

class ConflictException(BusinessException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)