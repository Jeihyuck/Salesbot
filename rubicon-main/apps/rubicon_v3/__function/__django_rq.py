import enum
import time
import pydantic

from django_rq import get_queue
from django_rq.queues import Queue
from rq.job import Job
from rq import Retry
from typing import Dict, Any, List, Tuple, Optional


class Status(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DjangoRqResult(pydantic.BaseModel):
    status: Status
    result: Any = None
    error: str = None
    elapsed_time: float | None = None


def enqueue_dynamic_jobs(
    function_params: List[
        Tuple[callable, tuple, dict, Optional[str], Optional[str]]
    ],  # TODO: Add retry?
) -> Dict[str, str]:
    """
    여러 작업을 큐에 넣고 작업 이름을 작업 ID에 매핑하는 사전을 반환합니다.

    Args:
        function_params (List[Tuple[callable, tuple, dict, Optional[str]]]):
            (함수, 인수, 키워드 인수, 첫 번째 식별자, 두 번째 식별자) 튜플 목록. 식별자는 선택사항입니다.

        - 함수 (callable): 실행할 함수.
        - 인수 (tuple): 위치 인수의 튜플.
        - 키워드 인수 (dict): 키워드 인수의 사전.
        - 첫 번째 식별자 (Optional[str]): 첫 번째 식별자.
        - 두 번째 식별자 (Optional[str]): 두 번째 식별자.
    Returns:
        Dict[str, str]: 작업 이름을 작업 ID에 매핑하는 사전.
    """
    queue: Queue = get_queue("default")
    job_mapping = {}

    for func, args, kwargs, identifier_1, identifier_2 in function_params:
        func_name = func.__name__

        # Use identifier if provided, otherwise just use function name
        if identifier_1:
            job_name = f"{func_name}__{identifier_1}"
            if identifier_2:
                job_name = f"{job_name}__{identifier_2}"
        else:
            job_name = func_name

        # Get the function path as a string
        function_path = f"{func.__module__}.{func.__name__}"

        # Enqueue the job using the string path to the function
        job = queue.enqueue(function_path, *args, **kwargs)
        job_mapping[job_name] = job.id

    return job_mapping


def get_all_results(
    job_mapping: Dict[str, str], timeout: int = 10
) -> Dict[str, DjangoRqResult]:
    """
    모든 작업의 결과를 가져옵니다.

    Args:
        job_mapping (Dict[str, str]): 작업 이름을 작업 ID에 매핑하는 사전.
        timeout (int, optional): 타임아웃 시간(초). 기본값은 10초입니다.

    Returns:
        Dict[str, Any]: 작업 이름을 결과에 매핑하는 사전.
    """

    def get_elapsed_time(job: Job) -> Optional[float]:
        if job.ended_at and job.started_at:
            return (job.ended_at - job.started_at).total_seconds()
        return None

    queue: Queue = get_queue("default")
    start_time = time.time()
    results = {}

    while time.time() - start_time < timeout:
        all_finished = True

        for func_name, job_id in job_mapping.items():
            if func_name not in results:
                job = queue.fetch_job(job_id)
                if job is None:
                    # Job doesn't exist anymore
                    results[func_name] = DjangoRqResult(
                        status=Status.FAILED,
                        error="Job not found",
                        elapsed_time=None,
                    )
                elif job.is_finished:
                    results[func_name] = DjangoRqResult(
                        status=Status.SUCCESS,
                        result=job.result,
                        elapsed_time=get_elapsed_time(job),
                    )
                elif job.is_failed:
                    results[func_name] = DjangoRqResult(
                        status=Status.FAILED,
                        error=job.exc_info,
                        elapsed_time=get_elapsed_time(job),
                    )
                else:
                    all_finished = False

        if all_finished:
            break

        time.sleep(0.05)

    # Handle timeouts and cancel remaining jobs
    for func_name, job_id in job_mapping.items():
        if func_name not in results:
            job = queue.fetch_job(job_id)

            if job is not None:
                try:
                    # Cancel/kill the running job
                    job.cancel()
                except Exception as e:
                    print(f"Failed to cancel job {job_id}: {e}")

            results[func_name] = DjangoRqResult(
                status=Status.TIMEOUT,
                error="Job timed out and was cancelled",
                elapsed_time=get_elapsed_time(job) if job else None,
            )

    return results


def run_job_high(func: callable, args: tuple, kwargs: dict, retry: int = 3):
    """
    단일 작업을 백그라운드에서 실행하도록 큐에 넣습니다. HIGH RQ WORKER

    Args:
        func (callable): 실행할 함수.
        args (tuple, optional): 위치 인수의 튜플. 기본값은 빈 튜플입니다.
        kwargs (dict, optional): 키워드 인수의 사전. 기본값은 빈 사전입니다.
    """
    queue = get_queue("high")

    # Get the function path as a string (this is key)
    function_path = f"{func.__module__}.{func.__name__}"

    queue.enqueue(function_path, *args, **kwargs, retry=Retry(max=retry))


def run_job_default(func: callable, args: tuple, kwargs: dict, retry: int = 3):
    """
    단일 작업을 백그라운드에서 실행하도록 큐에 넣습니다. DEFAULT RQ WORKER

    Args:
        func (callable): 실행할 함수.
        args (tuple, optional): 위치 인수의 튜플. 기본값은 빈 튜플입니다.
        kwargs (dict, optional): 키워드 인수의 사전. 기본값은 빈 사전입니다.
    """
    queue = get_queue("default")

    # Get the function path as a string (this is key)
    function_path = f"{func.__module__}.{func.__name__}"

    queue.enqueue(function_path, *args, **kwargs, retry=Retry(max=retry))
