import json
from redis import Redis

from pymongo import MongoClient

from transformers import pipeline

import torch
import os

import re



sentiment = pipeline("sentiment-analysis", framework="pt")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
#mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.myLearningDB
collection = db.posts

#redis_client = Redis(host='localhost', port=6379, decode_responses=True)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

#mygroup consumer group exists, created CREATE posts mygroup $ MKSTREAM
try:
    redis_client.xgroup_create('posts', 'mygroup', id='0', mkstream=True)
    print("Created consumer group 'mygroup' for stream 'posts'")
except Exception as e:
    print(f"Consumer group setup: {e}")

while True:
    messages = redis_client.xreadgroup(
        groupname='mygroup',
        consumername='consumer1',
        streams={'posts': '>'},
        count=10,
        block=5000  # wait up to 5 seconds if no messages
    )

    if not messages:
        # No new entries arrived in the last 5 seconds
        continue

    for stream, entries in messages:
        for message_id, fields in entries:
            try:
                print(f"Stream: {stream}, ID: {message_id}")
                print(f"  text: {fields['text']}")
                print(f"  user: {fields['user']}")
                print(f"  timestamp: {fields['timestamp']}")
                result = sentiment(fields['text'])[0]
                label = result['label']
                score = result['score']
                print(f"  sentiment: {label}, score: {score}")

                document = {
                    "id" : message_id,
                    "text": fields['text'],
                    "user": fields['user'],
                    "timestamp": fields['timestamp'],
                    "label": label,
                    "score": score
                }

                sentiment_key = label.lower() 
                redis_client.hincrby("sentiment_count", sentiment_key,1)

                hashtags = re.findall(r"#\w+", fields['text'])
                print("  regex pattern:", r"#\w+")
                print("  matched hashtags:", hashtags)
                if hashtags:
                    print(f"  found hashtags: {hashtags}")

                for tag in hashtags:
                    # Increment the count for each hashtag
                    redis_client.hincrby("hashtag_counts", tag, 1)

                db.posts.insert_one(document)
                print(f"Inserted document into MongoDB with message id: {message_id}")

                redis_client.xack('posts', 'mygroup', message_id)
            except Exception as e:
                print(f"Error processing message {message_id}: {e}")
