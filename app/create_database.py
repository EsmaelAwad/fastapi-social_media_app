from app.database_functions import FastApiDatabaseConnector
from app.database_functions import AddColumnIfNotExists

# Connect to PostgreSQL server (to the default 'postgres' database)
connection, cursor = FastApiDatabaseConnector()

# Enable autocommit mode to run the CREATE DATABASE command
connection.autocommit = True

# Check if the database already exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'fastapi'")
exists = cursor.fetchone()

if not exists:
    # Create the database if it does not exist
    create_db_query = "CREATE DATABASE fastapi"
    cursor.execute(create_db_query)
    print("Database 'fastapi' created successfully!")
else:
    print("Database 'fastapi' already exists.")

# Close the connection
cursor.close()
connection.close()


# Connect to FastAPI server
connection, cursor = FastApiDatabaseConnector()

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
""")

tables = cursor.fetchall()

# 2. Get the structure (columns, data types) of each table
for table in tables:
    table_name = table[0]
    print(f"\nStructure of table: {table_name}")
    
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
    """)
    columns = cursor.fetchall()
    
    for column in columns:
        print(f"Column: {column[0]}, Type: {column[1]}, Nullable: {column[2]}, Default: {column[3]}")

connection.close()


connection, cursor = FastApiDatabaseConnector()
# Create a new table
create_table_query = """
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(250),  -- title cannot exceed 250 characters
    content VARCHAR(10000) NOT NULL,  -- content cannot be null and is limited to 10000 characters
    published BOOLEAN NOT NULL DEFAULT FALSE  -- published cannot be null and defaults to False
)
"""

cursor.execute(create_table_query)

# Example usage:
connection, cursor = FastApiDatabaseConnector()

# Add created_at column if not exists
AddColumnIfNotExists(
    table_name="posts", 
    column_name="created_at", 
    column_type="TIMESTAMP", 
    nullable=False, 
    default="NOW()", 
    connection=connection
)

# Add updated_at column if not exists
AddColumnIfNotExists(
    table_name="posts", 
    column_name="updated_at", 
    column_type="TIMESTAMP", 
    nullable=True, 
    connection=connection
)


# Add email column if not exists
AddColumnIfNotExists(
    table_name="posts", 
    column_name="email", 
    column_type="VARCHAR(250)", 
    nullable=True, 
    connection=connection
)

# creating users table
# Connect to PostgreSQL server (to the default 'postgres' database)
connection, cursor = FastApiDatabaseConnector()

# Create a new table
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,         -- Auto-incrementing unique user ID
    phone_number VARCHAR(15),           -- Phone number as string, with a limit of 15 characters
    email VARCHAR(255) UNIQUE NOT NULL, -- Email address, must be unique and cannot be NULL
    password VARCHAR(32) NOT NULL,      -- Password, Cannot be null
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of when the user was created, defaults to now
    city VARCHAR(100),                  -- City where the user resides
    country VARCHAR(100)                -- Country where the user resides
)
"""

cursor.execute(create_table_query)
connection.commit()
connection.close()


# Connect to PostgreSQL server (to the default 'postgres' database)
connection, cursor = FastApiDatabaseConnector()

# Create a new table for post likes
create_table_query = """
CREATE TABLE IF NOT EXISTS post_likes (
    post_id INT NOT NULL,               -- The ID of the post being liked
    email VARCHAR(255) NOT NULL,               -- The email of the user who liked the post
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the like was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the like was last updated
    current_status INT NOT NULL DEFAULT 0,          -- What is the status of the post for that user, like 1, dislike -1 , netural 0
    PRIMARY KEY (post_id, email),     -- Composite primary key: post_id + user_id
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,  -- Foreign key constraint on posts
    FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE   -- Foreign key constraint on users
)
"""

cursor.execute(create_table_query)
connection.commit()
connection.close()


