import os
import pandas as pd
from flask import Flask, request, jsonify, render_template

# Initialize Flask app
app = Flask(__name__)

# Path to save uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create a route for the home page to render HTML form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads and process the Excel file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part in the request"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No file selected"
    
    if file:
        # Save the uploaded file to the server
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Read the Excel file to extract phone numbers
        try:
            df = pd.read_excel(file_path)
            # Assuming the column name for phone numbers is "PhoneNumber"
            phone_numbers = df['PhoneNumber'].tolist()

            # Create JSON response
            phone_json = {"phone_numbers": phone_numbers}
            
            # Print to console for debug
            print(phone_json)

            # Return the JSON object as the response
            return jsonify(phone_json)
        
        except Exception as e:
            return f"Error processing the Excel file: {str(e)}"

# Start the Flask server
if __name__ == '__main__':
    # Create the uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
