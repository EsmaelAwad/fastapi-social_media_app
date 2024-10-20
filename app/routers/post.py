from app.database_functions import FastApiDatabaseConnector, DropPost, UpdatePost, VoteManager,  insert_dataframe_to_table, read_table
from app.models import Post, verify_post_owner, Vote 
import pandas as pd
from fastapi import Depends, HTTPException, Response, status, APIRouter
from app.routers.oauth2 import decode_access_token
from sqlalchemy import text

connection, cursor = FastApiDatabaseConnector()
router = APIRouter(
    tags=['Posts']
)


@router.post('/posts/create')
def make_post_with_schema(new_post: Post, token_data: dict = Depends(decode_access_token)):
    """
    Create a new post.

    Requires:
        - The title of the post.
        - The content of the post.
        - The publication status of the post (true for published, false for draft). Defaults to true.

    Parameters:
    - new_post (Post): The Pydantic model that contains the title, content, and published status of the post.
    - user_email (str, optional): The user's email, automatically extracted from the token via the 'decode_access_token' dependency.

    Returns:
    - JSON response containing the post details and a success message.

    Example:
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/posts/create' \
      -H 'Authorization: Bearer <token>' \
      -d '{"title": "My First Post", "content": "Hello World!", "published": true}'
    ```
    Expected Response:
    ```json
    {
        "Message": "Successfully Created Your Post",
        "Your Post Title": "My First Post",
        "Your Post Content": "Hello World!",
        "Your Post Status": "Published"
    }
    ```
    """
    email = token_data.get('user_email')
    post_dict = new_post.model_dump()
    payload_title = post_dict.get('title')
    payload_content = post_dict.get('content')
    payload_publish_choice = post_dict.get('published')

    post_status = "Published" if payload_publish_choice else "Drafted"
    post_df = pd.DataFrame(
        {
            'title': [payload_title],
            'content': [payload_content],
            'published': [payload_publish_choice],
            'email': [email]
        }
    )
    insert_dataframe_to_table(post_df, 'posts')

    return {
        "Message": "Successfully Created Your Post",
        "Your Post Title": payload_title,
        "Your Post Content": payload_content,
        "Your Post Status": post_status,
    }

@router.get('/posts/get-user-posts')
def get_posts(token_data: dict = Depends(decode_access_token), 
              limit: int = 10, skip: int = 0, 
              sortby_date_ascending: str = 'asc', 
              contains: str = ""):
    """
    Retrieve all user posts with optional filtering, pagination, and sorting.

    Args:
    - token_data (dict): User authentication information, automatically extracted from the token via the 'decode_access_token' dependency.
    - limit (int, optional): The maximum number of posts to retrieve. Default is 10.
    - skip (int, optional): The number of posts to skip for pagination. Default is 0.
    - sortby_date_ascending (str, optional): The sorting order of the posts by `created_at`. Accepts 'asc' for ascending or 'desc' for descending. Default is 'asc'.
    - contains (str, optional): A string to filter posts by searching for this value in the title or content. Default is an empty string, which means no filtering.

    Raises:
    - HTTPException: If an invalid `sortby_date_ascending` value is provided (anything other than 'asc' or 'desc').

    Returns:
    - JSON response containing the posts in the database in the following format:
      ```json
      {
        "data": {
          "id": {
            "0": 1,
            "1": 2,
            "2": 3,
            "3": 4
          },
          "other_column": {
            "0": "other_column_value1",
            "1": "other_column_value2",
            "2": "other_column_value3",
            "3": "other_column_value4"
          }
        }
      }
      ```

    Query Logic:
    - If `contains` is provided, the query performs a case-insensitive `LIKE` search on the `title` and `content` columns.
    - The posts are sorted by `created_at` in either ascending ('asc') or descending ('desc') order based on the `sortby_date_ascending` parameter.
    - Pagination is handled using `limit` and `skip`, which limit the number of posts returned and determine the offset for pagination, respectively.

    Example Usage:
    1. **Retrieve posts with pagination and sorting**:
       ```bash
       curl -X 'GET' \
         'http://localhost:8000/posts/get-user-posts?skip=0&limit=5&sortby_date_ascending=desc' \
         -H 'Authorization: Bearer <token>'
       ```

    2. **Retrieve posts filtered by a keyword (`contains`) in title or content**:
       ```bash
       curl -X 'GET' \
         'http://localhost:8000/posts/get-user-posts?skip=0&limit=5&contains=example' \
         -H 'Authorization: Bearer <token>'
       ```
    """
    # Validate the sortby_date_ascending parameter
    if sortby_date_ascending not in ('asc', 'desc'):
        raise HTTPException(403, detail=f"The sortby_date_ascending query requires a value of either [asc, desc] but passed: {sortby_date_ascending}")

    if not contains:
        # Use parameterized query to avoid SQL injection risks
        query = text(f'''
            SELECT * FROM posts 
            ORDER BY created_at {sortby_date_ascending} 
            LIMIT :limit 
            OFFSET :skip
        ''')
        params = {"limit": limit, "skip": skip}
        users_posts = read_table(query, params=params)
    else:
        # Perform a LIKE search with parameterized query
        query = text(f'''
            SELECT * 
            FROM posts
            WHERE title LIKE :contains OR content LIKE :contains
            ORDER BY created_at {sortby_date_ascending}
            LIMIT :limit 
            OFFSET :skip
        ''')
        params = {"contains": f"%{contains}%", "limit": limit, "skip": skip}
        users_posts = read_table(query, params=params)

    return {'data': users_posts.to_dict()}

def find_post(id):# Running through the list
    users_posts = read_table('SELECT * FROM posts')
    return users_posts.loc[users_posts.id == id].to_dict()

@router.get('/posts/find-post/{id}')
def get_post(id: int, response: Response, token_data: dict = Depends(decode_access_token)):
    """
    Retrieve a specific post by ID.

    Parameters:
    - id (int): The ID of the post to retrieve.
    - user_email (str, optional): The user's email, automatically extracted from the token via the 'decode_access_token' dependency.

    Returns:
    - JSON response containing the post details if found, or an error message if not found.

    Example:
    ```bash
    curl -X 'GET' \
      'http://localhost:8000/posts/find-post/1' \
      -H 'Authorization: Bearer <token>'
    ```
    Expected Response:
    ```json
    {
        "id": 1,
        "title": "My First Post",
        "content": "Hello World!",
        "published": true
    }
    ```
    """
    p = find_post(id)
    if p:
        return p
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'Error': 'The ID you searched for seems to not be in our database.'}

@router.delete("/posts/delete-post/{id}")
def delete_post(id: int, token_data: dict = Depends(decode_access_token)):
    """
    Delete a post by its ID.

    This endpoint allows users to delete their own posts. The user's ownership of the post is verified using the email 
    extracted from the JWT token provided in the Authorization header.

    Parameters:
    - **id** (`int`): The ID of the post to delete.
    - **token_data** (`dict`, optional): This contains the user's email and other information from the JWT, extracted via the 'decode_access_token' dependency.

    Returns:
    - A JSON response confirming the deletion or an error message if the post does not exist or the user is not authorized.

    Example Usage:
    ```bash
    curl -X 'DELETE' \
      'http://localhost:8000/posts/delete-post/1' \
      -H 'Authorization: Bearer <your_token>'
    ```

    Possible Responses:
    - **200 OK**: If the post is successfully deleted, a confirmation message will be returned.
    - **403 Forbidden**: If the user is not the owner or the post does not exist, an appropriate error message will be returned.
    """
    verify_post_owner(id, token_data.get('user_email'))

    message = DropPost(id, connection)
    return {'Message': message}

@router.put('/posts/update-post/{id}')
def update_post(id: int, post: Post, token_data: dict = Depends(decode_access_token)):
    """
    Update a post by its ID.

    This endpoint allows users to update their own posts. The user's ownership of the post is verified using the email 
    extracted from the JWT token provided in the Authorization header.

    Parameters:
    - **id** (`int`): The ID of the post to update.
    - **post** (`Post`): The updated post details in the form of a Pydantic model (title, content, published).
    - **token_data** (`dict`, optional): This contains the user's email and other information from the JWT, extracted via the 'decode_access_token' dependency.

    Returns:
    - A JSON response confirming the update or an error message if the post does not exist or the user is not authorized.

    Example Usage:
    ```bash
    curl -X 'PUT' \
      'http://localhost:8000/posts/update-post/1' \
      -H 'Authorization: Bearer <your_token>' \
      -d '{"title": "Updated Post", "content": "Updated content", "published": false}'
    ```

    Possible Responses:
    - **200 OK**: If the post is successfully updated, a confirmation message will be returned.
    - **403 Forbidden**: If the user is not the owner or the post does not exist, an appropriate error message will be returned.
    """
    verify_post_owner(id, token_data.get('user_email'), method='update')
    message = UpdatePost(id, post.model_dump(), connection)
    return {'Message': message}

@router.post('/posts/like-post/{id}')
def like_post(vote: Vote, token_data: dict = Depends(decode_access_token)):
    """
    Like, dislike, or neutralize a post by its ID.

    This endpoint allows users to vote on a specific post by liking, disliking, or neutralizing their vote.
    The user's action is based on the provided direction of vote (-1 for dislike, 0 for neutral, and 1 for like).
    The user's email is extracted from the JWT token via the 'decode_access_token' dependency.

    Parameters:
    - **vote** (`Vote`): The vote object containing `direction_of_vote` (-1, 0, or 1) and `id_` (the post ID).
    - **token_data** (`dict`, optional): Contains the user's email and other details from the JWT token, extracted via the 'decode_access_token' dependency.

    Returns:
    - A JSON response confirming the vote change or raising an error if the vote is invalid.

    HTTP Exceptions:
    - **401 Unauthorized**: If the `direction_of_vote` is not valid (-1, 0, 1).
    - **404 Not Found**: If the post with the provided ID is not found in the `post_likes` table.

    Example Usage:
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/posts/like-post/1' \
      -H 'Authorization: Bearer <your_token>' \
      -d '{"direction_of_vote": 1, "id_": 1}'
    ```

    Expected Responses:
    - **200 OK**: If the vote was successfully updated or inserted, returns a confirmation message.
    - **Keys if response is OK**:
      - total_likes: This should be used to indicate how many overall likes in a post.
      - total_negative_votes
      - total_interactions
    - **404 Not Found**: If the post ID is invalid or the user does not have any interaction with the post.
    """
    direction_of_vote = vote.direction_of_vote
    id_ = vote.id_

    # Validate direction_of_vote
    if direction_of_vote not in (-1, 0, 1):
        raise HTTPException(status_code=401, detail='Forbidden, user can only like, dislike, or neutralize.')

    # Check if the user has already interacted with this post
    user_post_like_status = read_table('''
        SELECT 
            post_id,
            email,
            current_status
        FROM post_likes 
        WHERE post_id = :id AND email = :email
        ''', params={'id': id_, 'email': token_data.get('user_email')})

    # If the post does not exist for the user, raise an exception
    if user_post_like_status is None:
        raise HTTPException(status_code=404, detail='Post not found or user has no previous interaction with this post.')

    # Prepare data for the VoteManager
    data = {'post_id': id_, 'email': token_data.get('user_email')}

    # Case 1: New vote interaction
    if user_post_like_status.empty:
        VoteManager(data=data, method='add_new_vote', current_status=1, connection=connection)
    
    # Case 2: Update existing interaction
    else:
        user_last_choice = user_post_like_status.current_status[0]

        # Update the database based on the vote direction
        if direction_of_vote >= 0:
            VoteManager(data=data, method='update_vote', current_status=direction_of_vote, connection=connection)
        
        # If the vote is -1 (dislike), apply the appropriate logic
        elif direction_of_vote == -1:
            absolute_last_choice = abs(user_last_choice)
            current_status = absolute_last_choice + direction_of_vote
            VoteManager(data=data, method='update_vote', current_status=int(current_status), connection=connection)
    post_likes_query = """
  SELECT 
    SUM(CASE WHEN current_status > 0 THEN 1 ELSE 0 END) as total_likes,
    SUM(CASE WHEN current_status = -1 THEN 1 ELSE 0 END) as total_negative_votes,
    COUNT(current_status) as total_interactions
  FROM posts p 
  JOIN post_likes pl ON pl.post_id = p.id
"""
    post_likes = read_table(post_likes_query, conn=connection)
    return {'Message': 'Vote successfully recorded.',
            'total_likes': int(post_likes['total_likes'].iloc[0]),
            'total_negative_votes': int(post_likes['total_negative_votes'].iloc[0]),
            'total_interactions': int(post_likes['total_interactions'].iloc[0])}

