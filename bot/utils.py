from pymongo import MongoClient
import os

client = MongoClient(os.environ.get("MONGO_URI"))
db = client.get_default_database()
users = db.users

def get_user_data(user_id):
    """Fetch user data by Telegram user ID."""
    return users.find_one({"user_id": user_id})

def get_user_by_username(username):
    """Fetch user data by bot-generated username."""
    return users.find_one({"username": username})

def is_registered(user_id):
    """Check if user is registered."""
    return users.find_one({"user_id": user_id}) is not None

def register_user(user_id, gender, name):
    """Register a new user."""
    # Generate username if needed here or later
    users.update_one(
        {"user_id": user_id},
        {"$set": {"gender": gender, "name": name}},
        upsert=True
    )

def set_username(user_id, username):
    """Assign a bot-generated username to the user."""
    users.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}}
    )
