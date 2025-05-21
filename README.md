# Project Setup

Follow these steps to set up and run the project locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ambesh333/mlops_scheduler.git
    ```

2.  **Navigate to the project directory:**
    ```bash
    cd mlops_scheduler
    ```

3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment:**
    -   On Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

5.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

6.  **Run tests (Optional):**
    ```bash
    pytest -m test
    ```

7.  **Start PostgreSQL (using Docker):**
    ```bash
    docker run --name mlops_postgres \
      -e POSTGRES_USER=user \
      -e POSTGRES_PASSWORD=password \
      -e POSTGRES_DB=mlops \
      -p 5432:5432 \
      -d postgres
    ```

8.  **Start Redis (using Docker):**
    ```bash
    docker run --name redis-queue -p 6379:6379 -d redis
    ```

9.  **Run database migrations:**
    ```bash
    alembic upgrade head
    ```

10. **Start the FastAPI application:**
    ```bash
    uvicorn app.main:app --reload
    ```

11. **Start the scheduler script:**
    ```bash
    python -m app.core.run_deployments
    ```

The API will be available at `http://127.0.0.1:8000`.

## Database Schema

Here is a UML diagram representing the database schema:

![Database Schema UML Diagram](https://www.mermaidchart.com/raw/7a7e0ef6-1f87-4691-9a72-2e0fd2b27480?theme=light&version=v0.1&format=svg)

## Scheduling Algorithm

The scheduling algorithm works as follows:

*   **Filter out "impossible" jobs:** If a job asks for more resources than the system even has in total, it's skipped immediately.

*   **Score the jobs:** Jobs are scored based on how resource-intensive they are, with GPU-heavy jobs being treated as more important than CPU or RAM-heavy ones (because GPUs are scarcer or more valuable).

*   **Split jobs into two queues:**
    *   High Priority Queue – Important jobs that can preempt lower ones if needed.
    *   Low Priority Queue – Less important jobs that only run if there's leftover capacity.

*   **Try to schedule High Priority jobs first:**
    *   If there's space, they're added directly.
    *   If there isn't, the algorithm checks whether it can pause one or more low-priority jobs to make space.

*   **Then schedule Low Priority jobs:**
    *   Only added if they fit without disrupting anything else.
    *   They never cause preemption of other jobs.

*   **Return two results:**
    *   A list of jobs that are scheduled to run.
    *   A list of low-priority jobs that were stopped (preempted) to make room for high-priority ones.

## API Endpoints

Here is a list of the available API endpoints and their usage:

### User Endpoints

*   **Register User:**
    `POST /api/users/register`
    Body:
    ```json
    {
        "username": "ambesh4",
        "password": "ambesh"
    }
    ```

*   **Login User:**
    `POST /api/users/login`
    Body:
    ```json
    {
        "username": "ambesh2",
        "password": "ambesh"
    }
    ```

### Organization Endpoints

*   **Create Organization:**
    `POST /api/orgs/create`
    Body:
    ```json
    {
        "name":"org1"
    }
    ```

*   **Join Organization:**
    `POST /api/orgs/join`
    Body:
    ```json
    {
        "invite_code": "XNwDkZzK6Mc"
    }
    ```

*   **Get All Organizations:**
    `GET /api/orgs/all`

*   **Get User's Organizations:**
    `GET /api/orgs/my`

### Cluster Endpoints

*   **Create Cluster:**
    `POST /api/clusters`
    Body:
    ```json
    {
      "name": "cluster_higrh",
      "organization_id": 1,
      "total_cpu": 80000,
      "total_ram": 16384,
      "total_gpu": 2000
    }
    ```

*   **Get Cluster Deployments:**
    `GET /api/clusters/{cluster_id}/deployments`
    *(Replace `{cluster_id}` with the actual cluster ID)*

*   **Get Cluster Status:**
    `GET /api/clusters/{cluster_id}/status`
    *(Replace `{cluster_id}` with the actual cluster ID)*

### Deployment Endpoints

*   **Create Deployment:**
    `POST /api/deployments`
    Body:
    ```json
    {
      "cluster_id": 4,  
      "image": "nginx11", 
      "required_cpu": 20, 
      "required_ram": 10, 
      "required_gpu": 2,
      "priority": "HIGH" 
    }
    ```

*   **List Deployments for Cluster:**
    `GET /api/deployments?cluster_id={cluster_id}`
    *(Replace `{cluster_id}` with the actual cluster ID)*

*   **Get Deployment by ID:**
    `GET /api/deployments/{deployment_id}`


*   **Update/Other Deployment Operation (Based on User Example):**
    `POST /api/deployments/{deployment_id}`
    Body:
    ```json
    {
    "cluster_id": 1
    }
    ```

