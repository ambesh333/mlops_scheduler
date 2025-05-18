import redis
import json
import os

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def push_deployment_to_queue(deployment: dict):
    """Push deployment to Redis queue"""
    r.rpush("deployment_queue", json.dumps(deployment))
