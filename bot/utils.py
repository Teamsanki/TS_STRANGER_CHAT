from pymongo import MongoClient
import os

# Connect to MongoDB using the MONGO_URI environment variable
client = MongoClient(os.getenv("MONGO_URI"))
db = client["telemingle"]
users = db["users"]

def is_registered(user_id):
    """Check if a user is already registered."""
    return users.find_one({"user_id": user_id}) is not None

def register_user(user_id, gender, name):
    """Register a new user."""
    users.insert_one({
        "user_id": user_id,
        "gender": gender,
        "name": name
    })

def get_user_data(user_id):
    """Get a registered user's data (name and gender)."""
    return users.find_one({"user_id": user_id}) or {}
