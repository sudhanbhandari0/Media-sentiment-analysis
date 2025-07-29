from fastapi import FastAPI, Query
from pymongo import MongoClient
from typing import List, Dict
from redis import Redis
from fastapi.responses import StreamingResponse
import json, asyncio
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:8080"],  # your dashboard origin
  allow_methods=["GET"],
  allow_headers=["*"],
)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client.myLearningDB
posts_collection = db.posts

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/history", response_model=List[Dict])
def history(
    hashtag: str = Query(..., description="Hashtag to filter by, e.g. '#tech'"),
    since:   str = Query(..., description="ISO timestamp to filter from, e.g. '2025-07-28T00:00:00Z'")
):
    """
    Return all posts whose text contains the given hashtag
    and whose timestamp is >= the `since` parameter.
    """
    # Build MongoDB query
    query = {
        "text": {"$regex": hashtag, "$options": "i"},
        "timestamp": {"$gte": since}
    }

    # Execute the query, sort by timestamp ascending
    cursor = posts_collection.find(query).sort("timestamp", 1)

    # Format each document for JSON response
    results = []
    for doc in cursor:
        results.append({
            "id":        str(doc["_id"]),
            "text":      doc["text"],
            "user":      doc["user"],
            "timestamp": doc["timestamp"]
        })

    return results

@app.get('/metrics')
def metrics():
    """Return real time sentiment and hashtag count from redis"""

    sentiment_count = redis_client.hgetall("sentiment_count")
    sentiment = {k: int(v) for k, v in sentiment_count.items()}
    hashtags = redis_client.hgetall("hashtag_counts")
    hashtags = {k: int(v) for k, v in hashtags.items()}
    return {
        "sentiment_count": sentiment,
        "hashtags": hashtags
    }

async def metrics_invent_generator():
    """Async generator that yields the latest metrics as SSE-formatted strings. """
    last_payload = None
    first = True

    while True:
        sentiment_count = redis_client.hgetall("sentiment_count")
        sentiment = {k: int(v) for k, v in sentiment_count.items()}
        hashtags = redis_client.hgetall("hashtag_counts")
        hashtags = {k: int(v) for k, v in hashtags.items()}

        payload ={"sentiment": sentiment, "hashtags": hashtags}

        if payload != last_payload:
            first = False
            data_str = json.dumps(payload)
            yield f"data: {data_str}\n\n"
            last_payload = payload
        await asyncio.sleep(1)  # Adjust the sleep time as needed

@app.get('/metrics/stream')
async def metrics_stream():
    """Stream real-time metrics using Server-Sent Events (SSE)"""
    return StreamingResponse(metrics_invent_generator(), media_type="text/event-stream")


   


