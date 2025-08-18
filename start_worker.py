#!/usr/bin/env python3
"""
Simple RQ Worker Starter Script
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import app modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from rq import Worker, Queue
from redis import Redis

def main():
    # Connect to Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queue = Queue('ingest', connection=redis_conn)
    
    # Create and start worker
    print(f"Starting RQ worker for queue 'ingest' on {redis_url}")
    print("Press Ctrl+C to stop")
    
    worker = Worker([queue], connection=redis_conn)
    worker.work()

if __name__ == "__main__":
    main()
