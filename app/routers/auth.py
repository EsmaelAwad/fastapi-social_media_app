from fastapi import APIRouter
from app.models import Login
from app.database_functions import read_table
from app.routers.oauth2 import create_access_token

router = APIRouter(
    tags=['Authentication'] 
)


@router.post('/login')
def login(login_payload: Login):
    """
    Authenticate a user and generate an access token.

    This endpoint allows a user to log in by providing valid credentials (email and password).
    It verifies the provided credentials against the users in the database, and if successful,
    returns an access token to be used for further authentication in the system.

    ### Parameters:
    - **login_payload**: A Pydantic model containing the following fields:
      - **email** (`str`): The user's email address.
      - **password** (`str`): The user's password.

    ### Returns:
    - **200 OK**: Returns an access token and the token type (Bearer) if the credentials are correct.
    - **401 Unauthorized**: Returns an error message if the credentials do not match.

    ### Example Usage:

    ```bash
    curl -X POST \
      'http://localhost:8000/login' \
      -H 'Content-Type: application/json' \
      -d '{
        "email": "test@example.com",
        "password": "Password123!"
      }'
    ```

    ### Example Success Response:
    ```json
    {
      "access_token": "<your_generated_token>",
      "token_type": "bearer"
    }
    ```

    ### Example Failure Response:
    - **Authentication Failure (401)**:
    ```json
    {
      "Message": "Authentication Failed, Credentials Do Not Match"
    }
    ```

    ### Raises:
    - **Exception**: Raised for general errors during the authentication process.

    """

    get_user_info_query = """
    SELECT 
        password
    FROM users 
    WHERE email = :email
    """

    # Execute the parameterized query with the email value
    user_password = read_table(get_user_info_query, params={'email': login_payload.email})

    # Create an access token if the credentials match
    access_token = create_access_token(data={'user_email': login_payload.email})

    # Check if user exists and the password matches
    if not user_password.empty and user_password.iloc[0]['password'] == login_payload.password:
        return {'access_token': access_token, 'token_type': 'bearer'}
    else:
        return {'Message': 'Authentication Failed, Credentials Do Not Match'}