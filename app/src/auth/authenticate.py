from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from auth.oauth2 import verify_access_token
from datasource.config import get_settings
from services.auth.cookieauth import OAuth2PasswordBearerWithCookie
from jose import jwt, ExpiredSignatureError, JWTError

bearer_scheme = HTTPBearer(auto_error=True)

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

def authenticate(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login = str(payload.get("login"))
        if not login:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return login

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/signin")

# async def authenticate(token: str=Depends(oauth2_scheme)) -> str:
#     if not token:
#         raise HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="Sign in for access"
#         )
#     decoded_token = verify_access_token(token)
#     return decoded_token["login"]

oauth2_scheme_cookie = OAuth2PasswordBearerWithCookie(tokenUrl="/home/token")

async def authenticate_cookie(token: str=Depends(oauth2_scheme_cookie)) -> str:
    if not token:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sign in for access"
        )
    token = token.removeprefix('Bearer ')
    decoded_token = verify_access_token(token)
    return decoded_token["login"]
