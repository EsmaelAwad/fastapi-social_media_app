from pydantic import BaseModel, EmailStr, field_validator
from psycopg2.errors import UniqueViolation
from fastapi.exceptions import HTTPException
import pandas as pd 
from app.database_functions import read_table

"""
This file will contain all the tables we will create.

"""

# Now, We need to be explicit, the user cannot give what they want in the body, we want only: Title: Content. Nothing Less, Nothing More.
class Post(BaseModel):
    title:str 
    content:str 
    published:bool = True # Do you want to publish it or should it be a draft.

class User(BaseModel):
    phone_number: str
    email: EmailStr
    password: str
    city: str
    country: str

    # Validator to ensure city and country are properly capitalized
    @field_validator('city', 'country')
    def capitalize_fields(cls, value):
        return value.lower().capitalize()


class PasswordError(Exception):
    """Custom exception for password format errors."""
    pass


# Example of how to use this:
def validate_password(password: str):
    if len(password) <= 8:
        raise PasswordError("Password must be greater than 8 characters.")
    if not any(char.isupper() for char in password):
        raise PasswordError("Password must have at least 1 uppercase character.")
    if not any(char in "*&!#$%" for char in password):
        raise PasswordError("Password must have at least 1 special character like (*&!#$%).")

class EmailIsAlreadyUsed(UniqueViolation):
    pass 

class Login(BaseModel):
    email: EmailStr
    password: str  

def verify_post_owner(
                post_id: int,
                current_user_email: str,
                method='delete'
                ):
    """
    Verify the ownership of a post before allowing an action (delete or update).

    This function ensures that the current user is the owner of a specific post before they can perform an action like deleting or updating it.
    If the user is not the owner, or if the post does not exist, the function raises an HTTP 403 Forbidden error.

    ### Parameters:
    - **post_id** (`int`): The ID of the post to be verified.
    - **current_user_email** (`str`): The email address of the current user attempting the action.
    - **method** (`str`): The action being attempted on the post. Defaults to 'delete', but can also be 'update'. This value is included in the error message.

    ### Returns:
    - If the post exists and the user is the owner, the function allows the calling code to proceed.
    - If the post does not exist, the function raises an HTTP 403 error with the message: "The post you are trying to <method> does not exist."
    - If the post has no owner (the `email` field is `NULL`), the function raises an HTTP 403 error with the message: "This is a development post, unauthorized users cannot <method> it."
    - If the current user is not the owner of the post, the function raises an HTTP 403 error with the message: "The post is owned by <post_owner_email>, <current_user_email> is not authorized to <method> it."

    ### Raises:
    - **HTTPException(403)**: Raised in the following cases:
        1. The post does not exist.
        2. The post is a development post (has no owner).
        3. The current user is not the owner of the post.

    ### Example Usage:

    ```python
    try:
        verify_post_owner(post_id=1, current_user_email='user@example.com', method='delete')
        # If no exception is raised, the current user is allowed to delete the post.
    except HTTPException as e:
        print(e.detail)  # Handle the error (e.g., return the error message to the user).
    ```

    ### Example Response:

    - **Post Does Not Exist**:
    ```json
    {
        "detail": "The post you are trying to delete does not exist."
    }
    ```

    - **Unauthorized (Not Post Owner)**:
    ```json
    {
        "detail": "The post is owned by owner@example.com, user@example.com is not authorized to delete it."
    }
    ```

    """
    post_owner = read_table(
        f"""
    SELECT 
        email
    FROM posts
    WHERE id = {post_id}
    """
    )

    if post_owner.empty:
        raise HTTPException(403, detail=f'The post you are trying to {method} does not exist.')

    # Extract the email from the post_owner
    post_owner_email = post_owner.iloc[0]['email']

    # Check if email is NaN (NULL in the database)
    if pd.isna(post_owner_email):
        raise HTTPException(403, detail=f'This is a development post, unauthorized users cannot {method} it.')

    # Compare the post owner's email to the current user's email
    if not post_owner_email == current_user_email:
        raise HTTPException(403, detail=f'The post is owned by {post_owner_email}, {current_user_email} is not authorized to {method} it.')
