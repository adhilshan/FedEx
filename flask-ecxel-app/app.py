from flask import Flask
from fedex.routes import routes

app = Flask(__name__)

# Register the routes blueprint
app.register_blueprint(routes)

# Start the Flask server
if __name__ == '__main__':
    app.run(port=3000, debug=True)
