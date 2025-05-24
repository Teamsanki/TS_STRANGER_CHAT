from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client["telemingle"]
users = db["users"]

def is_registered(user_id):
    return users.find_one({"user_id": user_id})

def register_user(user_id, gender, name):
    users.insert_one({"user_id": user_id, "gender": gender, "name": name})
