import heapq
from collections import deque
from typing import List, Dict, Tuple

def schedule_jobs(
    job_queue: List[Dict],
    running_jobs: List[Dict],
    total_resources: Dict
) -> Tuple[List[Dict], List[Dict]]:

    # 0. Normalize and filter out impossible jobs
    def normalize(j):
        j['priority'] = j['priority'].upper()
        return j
    jobs = [normalize(dict(j)) for j in job_queue]
    # drop any job that demands more than total capacity
    jobs = [
        j for j in jobs
        if j['cpu'] <= total_resources['cpu']
        and j['ram'] <= total_resources['ram']
        and j['gpu'] <= total_resources['gpu']
    ]

    running = [normalize(dict(j)) for j in running_jobs]

    available = compute_available_resources(total_resources, running)
    scheduled_jobs: List[Dict] = []
    preempted_jobs: List[Dict] = []
    
    # scoring function: heavier weight to GPU, then CPU, then RAM
    def compute_score(job):
        return job['gpu'] * 100 + job['cpu'] * 10 + job['ram']

    for j in jobs:
        j['_score'] = compute_score(j)
    for j in running:
        j['_score'] = compute_score(j)

    # priority queues
    high_queue = deque(sorted(
        [j for j in jobs if j['priority'] == 'HIGH'],
        key=lambda x: x['_score'],
        reverse=True
    ))
    low_queue  = deque(sorted(
        [j for j in jobs if j['priority'] == 'LOW'],
        key=lambda x: x['_score'],
        reverse=True
    ))

    # min‑heap of low‑priority running jobs by score (negative so largest _score comes out first)
    low_running_heap = [(-j['_score'], j) for j in running if j['priority'] == 'LOW']
    heapq.heapify(low_running_heap)
    
    preempted_job_ids = set()

    # 1. Schedule HIGH priority
    while high_queue:
        job = high_queue.popleft()
        if fits(job, available):
            allocate(job, available)
            scheduled_jobs.append(job)
        else:
            success, to_preempt = try_preempt_heap(job, low_running_heap, available, preempted_job_ids)
            if success:
                for pj in to_preempt:
                    preempted_job_ids.add(id(pj))
                    deallocate(pj, available)
                    preempted_jobs.append(pj)
                allocate(job, available)
                scheduled_jobs.append(job)
            # else: leave job un‐scheduled

    # 2. Fill in LOW priority (no preemption for low)
    while low_queue:
        job = low_queue.popleft()
        if fits(job, available):
            allocate(job, available)
            scheduled_jobs.append(job)

    # 3. Clean up scores
    for j in scheduled_jobs + preempted_jobs + running:
        j.pop('_score', None)

    return scheduled_jobs, preempted_jobs


def compute_available_resources(total: Dict, running_jobs: List[Dict]) -> Dict:
    used_cpu = sum(j['cpu'] for j in running_jobs)
    used_ram = sum(j['ram'] for j in running_jobs)
    used_gpu = sum(j['gpu'] for j in running_jobs)
    return {
        'cpu': total['cpu'] - used_cpu,
        'ram': total['ram'] - used_ram,
        'gpu': total['gpu'] - used_gpu,
    }


def fits(job: Dict, avail: Dict) -> bool:
    return (
        avail['cpu'] >= job['cpu'] and
        avail['ram'] >= job['ram'] and
        avail['gpu'] >= job['gpu']
    )


def allocate(job: Dict, available: Dict):
    available['cpu'] -= job['cpu']
    available['ram'] -= job['ram']
    available['gpu'] -= job['gpu']


def deallocate(job: Dict, available: Dict):
    available['cpu'] += job['cpu']
    available['ram'] += job['ram']
    available['gpu'] += job['gpu']


def try_preempt_heap(
    job: Dict,
    low_running_heap: List[Tuple[int, Dict]],
    available: Dict,
    preempted_job_ids: set
) -> Tuple[bool, List[Dict]]:
    to_remove = []
    freed_cpu = freed_ram = freed_gpu = 0
    temp_heap = []

    while low_running_heap:
        score_neg, candidate = heapq.heappop(low_running_heap)
        if id(candidate) in preempted_job_ids:
            continue

        to_remove.append(candidate)
        freed_cpu += candidate['cpu']
        freed_ram += candidate['ram']
        freed_gpu += candidate['gpu']

        if fits(job, {
            'cpu': available['cpu'] + freed_cpu,
            'ram': available['ram'] + freed_ram,
            'gpu': available['gpu'] + freed_gpu,
        }):
            for entry in low_running_heap:
                heapq.heappush(temp_heap, entry)
            low_running_heap[:] = temp_heap
            heapq.heapify(low_running_heap)
            return True, to_remove
    for entry in to_remove:
        heapq.heappush(low_running_heap, (-entry['_score'], entry))
    return False, []

job_queue = [
    {
        'id': 'job1',          # Unique job identifier
        'priority': 'high',    # Priority: 'high' or 'low'
        'cpu': 2,              # CPU units required
        'ram': 4096,           # RAM in MB or GB (consistent unit)
        'gpu': 1               # GPU units required
    },
    {
        'id': 'job2',
        'priority': 'low',
        'cpu': 1,
        'ram': 2048,
        'gpu': 0
    },
    # ... more jobs
]

running_jobs = [
    {
        'id': 'jobA',
        'priority': 'low',
        'cpu': 1,
        'ram': 2048,
        'gpu': 0
    },
    {
        'id': 'jobB',
        'priority': 'low',
        'cpu': 2,
        'ram': 4096,
        'gpu': 1
    },
    # ... more running jobs
]

total_resources = {
    'cpu': 8,    # Total CPUs in the cluster
    'ram': 16384, # Total RAM available
    'gpu': 2     # Total GPUs available
}
