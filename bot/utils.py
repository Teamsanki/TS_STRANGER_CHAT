import os
from pymongo import MongoClient
import random
import string

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["tsbots"]  # Apna DB name yahan likho

users = db.users
usernames = db.usernames  # usernames collection for bot-generated usernames

def is_registered(user_id: int) -> bool:
    return users.find_one({"user_id": user_id}) is not None

def register_user(user_id: int, gender: str, name: str):
    if not is_registered(user_id):
        users.insert_one({
            "user_id": user_id,
            "gender": gender,
            "name": name,
            "username": None,
            "search_requests": []
        })

def get_user_data(user_id: int):
    return users.find_one({"user_id": user_id})

def update_username(user_id: int, username: str):
    users.update_one({"user_id": user_id}, {"$set": {"username": username}})
    usernames.insert_one({"username": username, "user_id": user_id})

def get_user_by_username(username: str):
    return usernames.find_one({"username": username})

def generate_random_username(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def add_search_request(target_user_id: int, from_user_id: int):
    users.update_one({"user_id": target_user_id}, {"$push": {"search_requests": from_user_id}})

def get_search_requests(user_id: int):
    user = get_user_data(user_id)
    return user.get("search_requests", []) if user else []

def clear_search_requests(user_id: int):
    users.update_one({"user_id": user_id}, {"$set": {"search_requests": []}})
