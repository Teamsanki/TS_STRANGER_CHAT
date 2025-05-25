import os
import random
import string
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URI"))
db_name = os.environ.get("DB_NAME", "ts_stranger_chat")
db = client[db_name]

users = db.users
active_chats = db.active_chats
pending_requests = db.pending_requests

def generate_random_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def is_registered(user_id):
    return users.find_one({"_id": user_id}) is not None

def register_user(user_id, gender, name):
    username = generate_random_username()
    users.update_one(
        {"_id": user_id},
        {"$set": {"gender": gender, "name": name, "username": username}},
        upsert=True
    )

def update_username(user_id):
    username = generate_random_username()
    users.update_one({"_id": user_id}, {"$set": {"username": username}})
    return username

def get_user_data(user_id):
    return users.find_one({"_id": user_id})

def get_user_by_username(username):
    return users.find_one({"username": username})

def save_active_chat(user1, user2):
    active_chats.insert_one({"user1": user1, "user2": user2})

def get_partner(user_id):
    chat = active_chats.find_one({"user1": user_id}) or active_chats.find_one({"user2": user_id})
    if chat:
        return chat["user2"] if chat["user1"] == user_id else chat["user1"]
    return None

def end_chat(user_id):
    active_chats.delete_many({"$or": [{"user1": user_id}, {"user2": user_id}]})
