from app.database_functions import insert_dataframe_to_table
from app.models import User, validate_password, PasswordError
from psycopg2.errors import UniqueViolation as EmailIsAlreadyUsed
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter

router = APIRouter(
    tags=['Users']
)
@router.post('/users/create-user')
def create_user(user: User):
    """
    Create a new user in the system.

    This endpoint allows for the creation of a new user by validating their password and saving their information
    (email, password, phone number, city, and country) in the 'users' database.

    ### Parameters:
    - **user**: A Pydantic model containing the user data to be inserted into the database.
        - **email** (`str`): The user's email address. Must be unique in the system.
        - **password** (`str`): The user's password. The password must satisfy the following criteria:
            - Must be greater than 8 characters.
            - Must contain at least one uppercase character.
            - Must contain at least one special character such as (*&!#$%).
        - **phone_number** (`str`): The user's phone number.
        - **city** (`str`): The user's city of residence.
        - **country** (`str`): The user's country of residence.

    ### Returns:
    - **200 OK**: If the user is successfully created, the response will contain:
      ```json
      {
        "Message": "The user has been successfully created"
      }
      ```
    - **400 Bad Request**: If the password does not meet the criteria, the response will return a message detailing the issue.
    - **409 Conflict**: If the email already exists in the system, a conflict message is returned.
    - **500 Internal Server Error**: For any other general error during the process.

    ### Raises:
    - **PasswordError**: Raised if the password fails to meet the validation criteria.
    - **IntegrityError**: Raised if there is a database constraint violation (e.g., duplicate email).
    - **Exception**: Raised for any other general exceptions.

    ### Example Usage:

    ```bash
    curl -X POST \
      'http://localhost:8000/users/create-user' \
      -H 'Content-Type: application/json' \
      -d '{
        "email": "test@example.com",
        "password": "Password123!",
        "phone_number": "1234567890",
        "city": "Cairo",
        "country": "Egypt"
      }'
    ```

    ### Example Response:

    - **Success (200 OK)**:
    ```json
    {
      "Message": "The user has been successfully created"
    }
    ```

    - **Password Validation Error (400)**:
    ```json
    {
      "Message": "Password must be greater than 8 characters, have at least 1 uppercase character, and 1 special character."
    }
    ```

    - **Email Conflict (409)**:
    ```json
    {
      "Message": "User was not created because the email passed is already used. Please try another email address."
    }
    ```

    - **General Error (500)**:
    ```json
    {
      "Message": "User was not created due to: <error message>"
    }
    ```

    """
    try:
        # Validate password
        validate_password(user.password)

        # Insert user data into the 'users' table
        insert_dataframe_to_table(user.model_dump(), 'users')  # Convert Pydantic model to dictionary
        
        return {'Message': "The user has been successfully created"}
    
    except PasswordError as e:
        return {'Message': str(e)}  # Return the custom error message from PasswordError
    
    except IntegrityError as e:
        # Check if the IntegrityError was caused by a UniqueViolation (email already exists)
        if isinstance(e.orig, EmailIsAlreadyUsed):
            return {'Message': "User was not created because the email passed is already used. Please try another email address."}
        return {'Message': f"User was not created due to: {str(e)}"}
    
    except Exception as e:
        return {'Message': f"User was not created due to: {str(e)}"}  # General error handling