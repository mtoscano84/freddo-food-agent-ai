from flask import Flask, send_from_directory, jsonify, request, redirect, send_file
from flask_cors import CORS
from google.cloud import storage
import os
import random
import logging
import sys
import io

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from freddo_agent import main as freddo_chat

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize GCS client
storage_client = storage.Client()
BUCKET_NAME = "freddo-recipe-store-gcs1"  # Replace with your bucket name
bucket = storage_client.bucket(BUCKET_NAME)

app = Flask(__name__)
CORS(app)

# Configure the path to your images directory
#IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'images')
IMAGES_DIR = '/Users/mtoscano/Sandbox/freddo-food-agent-ai/images'

@app.route('/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Backend is running'})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from GCS instead of local folder"""
    try:
        blob = bucket.blob(f"images/{filename}")
        
        # Get the image data from GCS
        image_data = blob.download_as_bytes()
        
        # Return the image with proper content type
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/png'  # Adjust if you have different image types
        )
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return "Image not found", 404

@app.route('/random-recipes')
def get_random_recipes():
    try:
        # List all blobs in the images directory
        blobs = list(bucket.list_blobs(prefix='images/'))
        images = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.png')]
        
        if not images:
            return jsonify({'error': 'No images found'}), 404
            
        selected = random.sample(images, min(10, len(images)))
        recipes = [{'name': f.split('.')[0], 'image': f} for f in selected]
        
        return jsonify({'recipes': recipes})
    except Exception as e:
        logger.error(f"Error getting recipes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        logger.info(f"Received request data: {data}")
        
        if not data or 'message' not in data:
            logger.error('No message provided in request')
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        logger.info(f"Processing message: {user_message}")
        
        # Get response using the Freddo agent
        try:
            response = freddo_chat(user_message)
            logger.info(f"Agent response: {response}")
        except Exception as agent_error:
            logger.error(f"Agent error: {str(agent_error)}")
            raise
        
        return jsonify({
            'response': response,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 