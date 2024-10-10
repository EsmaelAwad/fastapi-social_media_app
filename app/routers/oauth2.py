from fastapi import HTTPException, Header
import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    """
    Create a JWT access token.

    This function generates a JSON Web Token (JWT) that contains the provided user data
    and an expiration time, using a predefined secret key and algorithm.

    ### Parameters:
    - **data** (`dict`): A dictionary containing user information to be included in the token payload (e.g., user email).

    ### Returns:
    - **encoded_jwt** (`str`): A JWT token string encoded with the HS256 algorithm, ready for authorization purposes.

    ### Example Usage:

    ```python
    user_data = {"user_email": "test@example.com"}
    token = create_access_token(data=user_data)
    print(token)  # Encoded JWT token
    ```

    ### Raises:
    - **None**: This function does not raise exceptions.

    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Token expiration set to 30 minutes
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(Authorization: str = Header(None)):
    """
    Decode and validate a JWT access token.

    This function extracts the JWT token from the 'Authorization' header, decodes it, and validates its signature and expiration.

    ### Parameters:
    - **Authorization** (`str`, Header): The Authorization header containing the JWT token in the format: "Bearer <token>".

    ### Returns:
    - **decoded_jwt** (`dict`): A dictionary containing the decoded token data (e.g., user email).

    ### Example Usage:

    ```python
    Authorization = "Bearer <your_token>"
    decoded_token = decode_access_token(Authorization)
    print(decoded_token)  # Decoded token payload
    ```

    ### Raises:
    - **HTTPException (401)**: Raised if the Authorization header is missing.
    - **HTTPException (401)**: Raised if the token is expired (ExpiredSignatureError).
    - **HTTPException (401)**: Raised if the token is invalid (InvalidTokenError).

    """
    if Authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = Authorization.split(" ")[1]  # Extract the token from the 'Bearer' format
    
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Decode and verify token
        return decoded_jwt
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")  # Token is expired
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")  # Token is invalid
