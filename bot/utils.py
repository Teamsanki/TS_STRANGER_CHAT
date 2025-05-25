import random
import string
from pymongo import MongoClient
import os

client = MongoClient(os.environ.get("MONGO_URI"))
db = client.get_default_database()
users = db.tsusers

def is_registered(user_id):
    return users.find_one({"_id": user_id}) is not None

def register_user(user_id, gender, name):
    username = generate_username()
    users.update_one(
        {"_id": user_id},
        {"$set": {"gender": gender, "name": name, "username": username}},
        upsert=True
    )
    return username

def get_user_data(user_id):
    return users.find_one({"_id": user_id})

def get_user_by_username(username):
    return users.find_one({"username": username})

def generate_username():
    return "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
