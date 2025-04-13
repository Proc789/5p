from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Flask app is working correctly."

if __name__ == "__main__":
    app.run()
