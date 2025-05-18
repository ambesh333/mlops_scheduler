# run_deployment.py

import os
import asyncio
import json
from collections import defaultdict

import redis.asyncio as redis

from app.core.algorithm import schedule_jobs as schedule_jobs_on_single_cluster
from app.core.scheduler_db import (
    fetch_running_deployments_from_db,
    fetch_all_cluster_resources_from_db,
    mark_jobs_running,
    requeue_jobs
)



REDIS_QUEUE_KEY="deployment_queue"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

async def get_redis_client():
    """Connects to Redis."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await r.ping()
        print("Connected to Redis")
        return r
    except redis.asyncio.ConnectionError as e:
        print(f"Could not connect to Redis: {e}")
        return None
    

async def run_scheduler_consumer():
    """Poll Redis queue, normalize jobs, group by cluster, and schedule them."""
    r = await get_redis_client()
    if not r:
        print("❌ Failed to connect to Redis; exiting.")
        return

    print(f"🔄 Polling Redis queue '{REDIS_QUEUE_KEY}' every 10s")
    while True:
        # 1) Fetch all queue messages
        raw_msgs = await r.lrange(REDIS_QUEUE_KEY, 0, -1)
        if raw_msgs:
            # Clear queue immediately to avoid duplicates
            await r.delete(REDIS_QUEUE_KEY)
            print(f"📥 Retrieved {len(raw_msgs)} new job(s) from queue")
        else:
            raw_msgs = []

        # 2) Deserialize and normalize keys
        normalized_jobs = []
        for msg in raw_msgs:
            try:
                job = json.loads(msg)
                normalized_jobs.append({
                    "id":         job["deployment_id"],
                    "priority":   job["priority"].upper(),
                    "cpu":        job["required_cpu"],
                    "ram":        job["required_ram"],
                    "gpu":        job["required_gpu"],
                    "cluster_id": job["cluster_id"],
                })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Skipping invalid queue message: {msg} ({e})")

        # 3) Group new jobs by cluster_id
        jobs_by_cluster: dict[int, list[dict]] = defaultdict(list)
        for job in normalized_jobs:
            jobs_by_cluster[job["cluster_id"]].append(job)

        # 4) Fetch current state from DB
        running = await fetch_running_deployments_from_db()
        resources = await fetch_all_cluster_resources_from_db()
        print(f"ℹ️  {len(running)} running job(s), {len(resources)} cluster(s) in system")

        # 5) For each cluster, schedule
        for cid, res in resources.items():
            new_jobs = jobs_by_cluster.get(cid, [])
            active   = [j for j in running if j["cluster_id"] == cid]
            if not new_jobs and not active:
                continue

            print(f"🔧 Scheduling cluster {cid}: {len(new_jobs)} new, {len(active)} running")
            scheduled, preempted = schedule_jobs_on_single_cluster(
                new_jobs,
                active,
                {"cpu": res["total_cpu"], "ram": res["total_ram"], "gpu": res["total_gpu"]}
            )

            if scheduled:
                print(f"✅ Scheduled on cluster {cid}: {[j['id'] for j in scheduled]}")
                await mark_jobs_running(cid, [j['id'] for j in scheduled])
            if preempted:
                print(f"⚠️  Preempted on cluster {cid}: {[j['id'] for j in preempted]}")
                await requeue_jobs(cid, [j['id'] for j in preempted])

        # 6) Sleep until next cycle
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_scheduler_consumer())


[{'deployment_id': 14, 'priority': 'HIGH', 'required_cpu': 20.0, 'required_ram': 10, 'required_gpu': 2, 'cluster_id': 4}]
[]
{'cpu': 80000.0, 'ram': 16384, 'gpu': 2000}