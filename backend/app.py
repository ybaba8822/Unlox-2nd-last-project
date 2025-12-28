from flask import Flask, jsonify, request
from pymongo import MongoClient, errors
import os
import time
from datetime import datetime

app = Flask(__name__)

mongo_host = os.environ.get("MONGO_HOST", "mongo")
mongo_port = int(os.environ.get("MONGO_PORT", 27017))

client = None
for _ in range(10):
    try:
        client = MongoClient(f"mongodb://{mongo_host}:{mongo_port}/", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("Connected to MongoDB!")
        break
    except errors.ServerSelectionTimeoutError:
        print("MongoDB not ready, retrying in 3 seconds...")
        time.sleep(3)

if client is None:
    raise Exception("Could not connect to MongoDB")

db = client.testdb

@app.route("/")
def home():
    return "Backend Service Running!"

@app.route("/data", methods=["POST"])
def insert_data():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in request body"}), 400

        doc = {
            "message": data["message"],
            "created_at": datetime.utcnow()
        }
        result = db.values.insert_one(doc)
        response = {
            "status": "success",
            "inserted_id": str(result.inserted_id),
            "message": doc["message"],
            "created_at": doc["created_at"].isoformat() + "Z"
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/all")
def get_all():
    try:
        items = []
        for doc in db.values.find():
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc:
                doc["created_at"] = doc["created_at"].isoformat() + "Z"
            items.append(doc)
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

