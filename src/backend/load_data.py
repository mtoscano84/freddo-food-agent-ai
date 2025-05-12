import psycopg2
from psycopg2 import Error
import pandas as pd
import numpy as np
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.types import HttpOptions
from tqdm import tqdm
import os
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

#client = genai.Client("True", "freddo-project", "us-central1")
#client = genai.Client(project="freddo-project", location="us-central1")
#client = genai.Client(http_options=HttpOptions(api_version="v1"))
client = genai.Client(vertexai=True, project="freddo-food-agent-ai", location="us-central1")

def load_db_config():
    """Load database configuration from db_config.params file"""
    db_params = {}
    try:
        with open('db_config.params', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=')
                    db_params[key.strip()] = value.strip()
        return db_params
    except FileNotFoundError:
        print("Error: db_config.params file not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)


def create_database_schema(db_params):
    """
    Creates the database schema for the recipe and store management system.
    
    Args:
        db_params (dict): Database connection parameters containing:
            - host
            - database
            - user
            - password
            - port
    """
    try:
        # Establish connection
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Create extensions if they don't exist
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        connection.commit()

        # Create tables
        create_tables_query = """
        -- Recipes Table
        CREATE TABLE IF NOT EXISTS Recipes (
            recipe_id SERIAL PRIMARY KEY,
            Name VARCHAR(255) NOT NULL,
            Ingredients TEXT,
            Description TEXT,
            Instructions TEXT,
            Category VARCHAR(50),
            Cousin VARCHAR(50),
            Difficulty VARCHAR(20),
            Picture_url VARCHAR(255),
            desc_emb VECTOR(768)
        );

        -- Stores Table
        CREATE TABLE IF NOT EXISTS Stores (
            store_id SERIAL PRIMARY KEY,
            Name VARCHAR(255) NOT NULL,
            City VARCHAR(100),
            Address VARCHAR(255),
            Review DECIMAL(10, 2) NOT NULL
        );

        -- Shopping Lists Table
        CREATE TABLE IF NOT EXISTS shopping_lists (
            list_id SERIAL,
            user_id INTEGER NOT NULL,
            items TEXT,
            status VARCHAR(50)
        );

        -- Products Table
        CREATE TABLE IF NOT EXISTS products (
            product_id SERIAL PRIMARY KEY,
            store_id INTEGER REFERENCES Stores(store_id),
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            stock INTEGER,
            unit_price DECIMAL(10, 2)
        );

        -- Orders Table
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            store_id INTEGER REFERENCES Stores(store_id),
            total DECIMAL(10, 2),
            shipping_address VARCHAR(255),
            Status VARCHAR(50),
            "Delivery method" VARCHAR(50)
        );
        -- Users Table
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            Address VARCHAR(255),
            city VARCHAR(100),
            Allergies TEXT
        );
        -- Policies Table
        CREATE TABLE IF NOT EXISTS policies (
            policy_id SERIAL PRIMARY KEY,
            store_id INTEGER REFERENCES Stores(store_id),
            Policy_name VARCHAR(255),
            Delivery_time VARCHAR(255),
            Fee VARCHAR(255)
        );
        """
        
        create_constraints = """
        -- Foreign Key Constraint for shopping_lists table
        ALTER TABLE shopping_lists
        ADD CONSTRAINT fk_user_shopping_lists
        FOREIGN KEY (user_id)
        REFERENCES users(user_id);

        -- Foreign Key Constraint for orders table
        ALTER TABLE orders
        ADD CONSTRAINT fk_user_orders
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id);

        ALTER TABLE orders
        ADD CONSTRAINT fk_store_orders
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id);

        -- Foreign Key Constraint for products table
        ALTER TABLE products
        ADD CONSTRAINT fk_store_products
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id);
        
        -- Foreign Key Constraint for the policies table
        ALTER TABLE policies
        ADD CONSTRAINT fk_store_policies
        FOREIGN KEY (store_id)
        REFERENCES Stores(store_id);
        """
        
        # Execute the query
        cursor.execute(create_tables_query)
        print("Database schema created successfully")
        cursor.execute(create_constraints)
        print("Constraints created successfully")
        # Commit the changes
        connection.commit()


    except (Exception, Error) as error:
        print(f"Error while creating database schema: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed")

def generate_recipe_embeddings():
    """
    Generate embeddings for recipe descriptions using Google's text-embedding-005 model
    and save to a new CSV with the embeddings column
    """
    # Read the recipes CSV file
    recipes_df = pd.read_csv('../../data/recipes.csv')
    
    # Initialize empty list to store embeddings
    embeddings = []

    # Generate embeddings for each description
    for description in tqdm(recipes_df['Description']):
        try:
            response = client.models.embed_content(model="text-embedding-005",contents=description)
            embedding = response.embeddings[0].values  # Access values of first embedding
            embeddings.append(embedding)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            embeddings.append(None)
    
    # Convert embeddings list to numpy array and then to list for storage
    embeddings_list = [list(emb) if emb is not None else None for emb in embeddings]
    
    # Add embeddings as new column
    recipes_df['desc_emb'] = embeddings_list
    
    # Save to new CSV file
    output_path = Path('../../data/recipes_with_embeddings.csv')
    recipes_df.to_csv(output_path, index=False)
    
    print(f"Embeddings generated and saved to {output_path}")

def add_location_columns(db_params):
    """
    Add location columns to stores and users tables and populate with coordinates
    """
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Add location columns
        cursor.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS location geography(Point, 4326);")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS location geography(Point, 4326);")

        # Update store locations
        store_locations = {
            1: (41.3846615, 2.1632721),
            2: (41.3838736, 2.1617879),
            3: (41.3804708, 2.1576444),
            4: (41.3778072, 2.1857617),
            5: (41.3809062, 2.1674322)
        }

        for store_id, coords in store_locations.items():
            cursor.execute(
                "UPDATE stores SET location = ST_MakePoint(%s, %s)::geography WHERE store_id = %s",
                (coords[0], coords[1], store_id)
            )

        # Update user locations
        user_locations = {
            1: (41.385273, 2.161236),
            2: (41.381694, 2.136222),
            3: (41.399485, 2.157001),
            4: (41.405514, 2.175198),
            5: (41.384529, 2.183633)
        }

        for user_id, coords in user_locations.items():
            cursor.execute(
                "UPDATE users SET location = ST_MakePoint(%s, %s)::geography WHERE user_id = %s",
                (coords[0], coords[1], user_id)
            )

        connection.commit()
        print("Location columns added and populated successfully")

    except (Exception, Error) as error:
        print(f"Error while adding location columns: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed")

def load_data_from_csv(db_params):
    """Load data from CSV files into database tables"""
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        
        # Define CSV files and corresponding table names
        csv_files = {
            'users.csv': 'users',
            'stores.csv': 'stores', 
 #           'orders.csv': 'orders',
            'products.csv': 'products',
            'recipes_with_embeddings.csv': 'recipes',
            'shopping_lists.csv': 'shopping_lists',
            'policies.csv': 'policies'
        }

        # Load each CSV file into its table
        for csv_file, table_name in csv_files.items():
            try:
                with open(f'../../data/{csv_file}', 'r') as f:
                    # Skip the header row
                    next(f)
                    # Use copy_expert with CSV format to handle escaped commas
                    copy_sql = f"""
                        COPY {table_name} FROM STDIN WITH 
                        CSV 
                        DELIMITER ',' 
                        NULL '' 
                        QUOTE '"'
                    """
                    cursor.copy_expert(sql=copy_sql, file=f)
                print(f"Data loaded successfully from {csv_file} into {table_name} table")
                connection.commit()
                
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                connection.rollback()

    except (Exception, Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed")

def generate_recipe_images(db_params):
    """Generate images for each recipe using Vertex AI Image Generation"""
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        
        # Get all recipe names from the database
        cursor.execute("SELECT name FROM recipes")
        recipes = cursor.fetchall()

        # Initialize Vertex AI
        vertexai.init(project="freddo-project", location="us-central1")
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

        # Create images directory if it doesn't exist
        if not os.path.exists('images'):
            os.makedirs('images')

        # Generate image for each recipe
        for recipe in tqdm(recipes, desc="Generating recipe images"):
            recipe_name = recipe[0]
            output_file = f"images/{recipe_name}.png"

            # Skip if image already exists
            if os.path.exists(output_file):
                continue

            try:
                with tqdm(total=1, desc=f"Generating image for {recipe_name}", leave=False) as pbar:
                    images = model.generate_images(
                        prompt=recipe_name,
                        number_of_images=1,
                        language="en",
                        aspect_ratio="1:1",
                        safety_filter_level="block_some",
                    )
                    pbar.update(1)
                
                with tqdm(total=1, desc=f"Saving image for {recipe_name}", leave=False) as pbar:
                    images[0].save(location=output_file, include_generation_parameters=False)
                    pbar.update(1)
                
            except Exception as e:
                print(f"Error generating image for {recipe_name}: {e}")

    except (Exception, Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed")

def update_recipe_picture_urls(db_params):
    """
    Updates the picture_url column in the recipes table with the path to generated images.
    
    Args:
        db_params (dict): Database connection parameters
    """
    try:
        # Establish connection
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Update picture_url for all recipes
        cursor.execute("""
            UPDATE recipes 
            SET picture_url = CONCAT('images/', name, '.png')
        """)
        
        # Commit the transaction
        connection.commit()
        print("Successfully updated picture URLs for all recipes")

    except (Exception, Error) as error:
        print(f"Error while updating picture URLs: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed")

if __name__ == "__main__":
    db_params = load_db_config()    
    create_database_schema(db_params)
    generate_recipe_embeddings()
    load_data_from_csv(db_params)
    add_location_columns(db_params)
    update_recipe_picture_urls(db_params)
#    generate_recipe_images(db_params)
