from typing import Any
import pandas as pd 
from sqlalchemy import create_engine, text 
import psycopg2 
from datetime import datetime
from app.config import settings 

def FastApiDatabaseConnector(host:str=settings.host,
                             database:str=settings.database,
                             user:str=settings.user,
                             password:str=settings.password,
                             port:str=settings.port):
    """
    Mainly used when user wants to connect to postgres specific database
    """
    connection = psycopg2.connect(
        host= host,
        database= database,
        user = user,
        password = password,
        port = port   
    )
    return connection, connection.cursor()

def read_table(sql_query: str,
               conn=None,
               db_url: str = settings.database_url,
               close_connection=False, params={}):
    """
    Executes a SQL query and returns the result as a pandas DataFrame.

    Args:
        sql_query (str): A string representing the SQL query to be executed.
        conn: (Optional) Compatibility parameter.
        db_url (str): A SQLAlchemy database connection URL.
        close_connection (bool): Whether to close the connection after executing the query.
        params (dict): Optional dictionary of parameters to pass into the SQL query for parameterized queries.

    Returns:
        DataFrame: SQL query result as a pandas DataFrame.

    Example Usage:

    1. **Without Parameters**:

        ```python
        sql_query = "SELECT * FROM users"
        result = read_table(sql_query, db_url=database_url)
        print(result)
        ```

    2. **With Parameters**:

        ```python
        sql_query = "SELECT * FROM users WHERE email = :email"
        params = {'email': 'user@example.com'}
        result = read_table(sql_query, db_url=database_url, params=params)
        print(result)
        ```

    """
    try:
        # Create a SQLAlchemy engine
        engine = create_engine(db_url)

        # Establish a connection
        with engine.connect() as connection:
            # Convert the SQL query to a SQLAlchemy text object if it's a string
            if isinstance(sql_query, str):
                sql_query = text(sql_query)
                
            # Use pandas to read SQL via the SQLAlchemy connection
            if params:
                table = pd.read_sql(sql_query, connection, params=params)
            else:
                table = pd.read_sql(sql_query, connection)
        
        return table
        
    except Exception as e:
        print(f"An error occurred while reading the table: {e}")
        raise
        
def insert_dataframe_to_table(data: dict, table_name: str, 
                              db_url: str = settings.database_url,
                              if_exists: str = 'append', index: bool = False):
    """
    Inserts a Pandas DataFrame into a PostgreSQL table.

    Args:
        data (dict or pd.DataFrame): The data to be inserted, passed as a dictionary or a Pandas DataFrame.
        table_name (str): The name of the table where the data will be inserted.
        db_url (str): The SQLAlchemy database connection URL.
        if_exists (str): Action to take if the table already exists. Default is 'append'.
                         Other options: 'fail', 'replace'.
        index (bool): Whether to include the DataFrame's index as a column in the table. Default is False.

    Returns:
        None

    Raises:
        ValueError: If the data passed is neither a dictionary nor a Pandas DataFrame.
        Exception: For any other database-related errors.

    Usage Examples:

    1. Inserting data from a dictionary:
    
        data = {
            "title": ["Post 1", "Post 2"],
            "content": ["Content of post 1", "Content of post 2"],
            "published": [True, False]
        }
        insert_dataframe_to_table(data, "posts")
    
    2. Inserting data from an existing Pandas DataFrame:
    
        df = pd.DataFrame({
            "title": ["Post 3", "Post 4"],
            "content": ["Content of post 3", "Content of post 4"],
            "published": [True, True]
        })
        insert_dataframe_to_table(df, "posts")

    3. Specifying behavior when the table already exists:
    
        insert_dataframe_to_table(data, "posts", if_exists='replace')  # Replaces the table if it exists

    4. Including the DataFrame index as a column:
    
        insert_dataframe_to_table(data, "posts", index=True)
    """
    
    try:
        # Create a SQLAlchemy engine
        engine = create_engine(db_url)
        
        # Check if the data is a dictionary
        if isinstance(data, dict):
            # If the dictionary contains scalar values (not lists or iterables), wrap them in a list
            for key, value in data.items():
                if not isinstance(value, (list, tuple, set)):
                    data[key] = [value]  # Convert scalar values to lists
    
            # Create a DataFrame from the input dictionary
            df = pd.DataFrame(data)

        elif isinstance(data, pd.DataFrame):
            # Data is already a DataFrame
            df = data
        else:
            raise ValueError("The passed data object can only be a dictionary or a pandas DataFrame.")
        
        # Insert the DataFrame into the specified table
        df.to_sql(table_name, engine, if_exists=if_exists, index=index)
        
        print(f"Data inserted successfully into '{table_name}' table.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def DropPost(post_id: int, connection, close_connection=False):
    """
    Deletes a post by its ID from the posts table using psycopg2.

    Args:
        post_id (int): The ID of the post to be deleted.
        connection: A psycopg2 connection object.
        close_connection (bool): Whether to close the connection after deletion.
    
    Returns:
        None
    """
    try:
        # Create a cursor object
        cursor = connection.cursor()
        
        # SQL query to delete the post by ID
        delete_query = "DELETE FROM posts WHERE id = %s RETURNING *"
        
        # Execute the query with the post_id as a parameter
        cursor.execute(delete_query, (post_id,))
        
        deleted = cursor.fetchone()

        # Commit the transaction
        connection.commit()
        
        if deleted:
            return 'Post is successfully deleted.'
        else: 
            return 'Post was already deleted or does not exist.'
        
    except Exception as e:
        print(f"An error occurred while deleting the post: {e}")
        raise
    finally:
        # Close the connection if requested
        if close_connection:
            connection.close()

def UpdatePost(post_id: int, updates: dict, connection, close_connection=False):
    """
    Updates a post by its ID in the posts table using psycopg2.

    Args:
        post_id (int): The ID of the post to be updated.
        updates (dict): A dictionary containing the fields to be updated (e.g., {"title": "New Title"}).
        connection: A psycopg2 connection object.
        close_connection (bool): Whether to close the connection after the update.
    
    Returns:
        str: Message indicating the status of the update.
    """
    try:        
        # Remove 'id' field from updates if it exists (it should not be updated)
        if 'id' in updates:
            del updates['id']
        
        # Ensure there are still fields to update
        if not updates:
            return 'No valid fields to update.'

        # Add the updated_at field with the current timestamp
        updates['updated_at'] = datetime.now()

        # Create a cursor object
        cursor = connection.cursor()
        
        # Prepare the SQL query dynamically based on the fields to update
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        sql_query = f"UPDATE posts SET {set_clause} WHERE id = %s RETURNING *"
        
        # Get the values to update and append the post_id at the end
        values = list(updates.values()) + [post_id]
        
        # Execute the query with the provided values
        cursor.execute(sql_query, values)
        
        # Fetch the updated post
        updated_post = cursor.fetchone()

        # Commit the transaction
        connection.commit()
        
        if updated_post:
            return 'Post updated successfully.'
        else:
            return 'Post does not exist or was already deleted.'
    
    except Exception as e:
        print(f"An error occurred while updating the post: {e}")
        raise
    finally:
        # Close the connection if requested
        if close_connection:
            connection.close()


def AddColumnIfNotExists(table_name: str, column_name: str, column_type: str, 
                             nullable: bool = True, default: str = None, 
                             primary_key: bool = False, unique: bool = False, 
                             connection=None, close_connection=False):
    """
    Adds a column to a PostgreSQL table if it does not already exist.
    
    Args:
        table_name (str): The name of the table.
        column_name (str): The name of the column to add.
        column_type (str): The data type of the column (e.g., TIMESTAMP, VARCHAR(255), INTEGER).
        nullable (bool): Whether the column can be NULL. Default is True.
        default (str): The default value for the column, if applicable.
        primary_key (bool): Whether the column should be a primary key. Default is False.
        unique (bool): Whether the column should have a unique constraint. Default is False.
        connection: A psycopg2 connection object.
        close_connection (bool): Whether to close the connection after executing the query.
    
    Returns:
        None
    """
    try:
        # Create a cursor object
        cursor = connection.cursor()

        # Build the alter table query dynamically
        alter_query = f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='{table_name}' 
                AND column_name='{column_name}'
            ) THEN
                ALTER TABLE {table_name}
                ADD COLUMN {column_name} {column_type}
        """

        # Add NOT NULL constraint if necessary
        if not nullable:
            alter_query += " NOT NULL"

        # Add default value if provided
        if default:
            alter_query += f" DEFAULT {default}"

        # Add unique constraint if necessary
        if unique:
            alter_query += " UNIQUE"

        # Add primary key constraint if necessary
        if primary_key:
            alter_query += " PRIMARY KEY"

        # Close the query
        alter_query += "; END IF; END $$;"

        # Execute the query
        cursor.execute(alter_query)

        # Commit the changes
        connection.commit()

        print(f"Column '{column_name}' added to table '{table_name}' successfully.")

    except Exception as e:
        print(f"An error occurred while adding the column: {e}")
        raise
    finally:
        # Close the connection if requested
        if close_connection:
            connection.close()

def VoteManager(data: dict, method: str = 'add_new_vote', 
                current_status: int = 1,connection=None, 
                close_connection: bool = False):
    """
    Manages votes for posts by adding or updating a vote record in the 'post_likes' table.

    This function can either add a new vote or update an existing vote based on the provided `method`.
    The `post_likes` table contains information about post likes and the status of the vote (e.g., liked, disliked, or neutral).

    Args:
        data (dict): A dictionary containing the following required keys:
                     - 'post_id' (int): The ID of the post being voted on.
                     - 'email' (str): The email of the user casting the vote.
        method (str): Determines whether to add a new vote or update an existing one.
                      Options: 'add_new_vote' (default), 'update_vote'.
        current_status (int): The status of the vote. Typically -1 (dislike), 0 (neutral), or 1 (like). Default is 1.
        connection: A psycopg2 connection object to the database.
        close_connection (bool): Whether to close the connection after the operation. Default is False.
    
    Returns:
        str: A message indicating the result of the operation (success or failure).
    
    Raises:
        Exception: For any database-related errors.
    
    Usage Examples:
    
    1. Adding a new vote:
    
        data = {"post_id": 1, "email": "user@example.com"}
        VoteManager(data, method='add_new_vote', current_status=1, connection=conn)

    2. Updating an existing vote:
    
        data = {"post_id": 1, "email": "user@example.com"}
        VoteManager(data, method='update_vote', current_status=-1, connection=conn)
    """
    
    try:
        # Get the user_id based on the email provided in the data
        cursor = connection.cursor()
        
        user_id = data['email']

        # Adding a new vote
        if method == 'add_new_vote':
            # Insert new vote
            insert_vote_query = """
            INSERT INTO post_likes (post_id, email, current_status, created_at, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            cursor.execute(insert_vote_query, (data['post_id'], user_id, current_status))
            connection.commit()
            return "New vote added successfully."
        
        # Updating an existing vote
        elif method == 'update_vote':

            # Update existing vote
            update_vote_query = """
            UPDATE post_likes
            SET current_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE post_id = %s AND email = %s
            """
            cursor.execute(update_vote_query, (current_status, data['post_id'], user_id))
            connection.commit()
            return "Vote updated successfully."
        
        else:
            return "Invalid method. Use 'add_new_vote' or 'update_vote'."
    
    except Exception as e:
        print(f"An error occurred while managing the vote: {e}")
        raise
    finally:
        # Close the connection if requested
        if close_connection and connection is not None:
            connection.close()
