import json
import os
from redis import Redis

#redis_client = Redis(host='localhost', port=6379, decode_responses=True)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

with open('ingestor/data/sample_posts.jsonl', 'r') as f:
    for line in f:
        post = json.loads(line)

        redis_client.xadd(
            'posts',
            fields = {"text": post['text'], "user": post['user'], "timestamp": post['timestamp']},
        )

        print(f"Pushed post by {post['user']} to Redis stream.")