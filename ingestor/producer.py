import json
from redis import Redis

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

with open('ingestor/data/sample_posts.jsonl', 'r') as f:
    for line in f:
        post = json.loads(line)

        redis_client.xadd(
            'posts',
            fields = {"text": post['text'], "user": post['user'], "timestamp": post['timestamp']},
        )

        print(f"Pushed post by {post['user']} to Redis stream.")