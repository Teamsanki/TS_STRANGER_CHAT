# bot/utils.py

import os
import random
import string
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["ts_stranger_chat"]  # change to your DB name
users = db.users
active_chats = db.active_chats

def get_user_data(user_id):
    return users.find_one({"_id": user_id})

def register_user(user_id, gender, name):
    if not get_user_data(user_id):
        username = generate_username()
        users.insert_one({
            "_id": user_id,
            "name": name,
            "gender": gender,
            "username": username
        })

def is_registered(user_id):
    return get_user_data(user_id) is not None

def generate_username():
    return "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

def assign_username(user_id):
    username = generate_username()
    users.update_one({"_id": user_id}, {"$set": {"username": username}})
    return username

def get_user_by_username(username):
    return users.find_one({"username": username})

# Active Chat Functions
def save_active_chat(user_id, partner_id):
    active_chats.update_one(
        {"_id": user_id},
        {"$set": {"partner_id": partner_id}},
        upsert=True
    )

def get_active_partner(user_id):
    data = active_chats.find_one({"_id": user_id})
    return data["partner_id"] if data else None

def delete_active_chat(user_id):
    active_chats.delete_one({"_id": user_id})

def is_user_busy(user_id):
    return get_active_partner(user_id) is not None
