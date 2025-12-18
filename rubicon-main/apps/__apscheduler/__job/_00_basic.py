import uuid
import logging
from datetime import timedelta
from django.utils import timezone
# from django.conf import settings

from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)

from alpha.settings import INSTANCE_ID
import alpha._db as DB
import alpha._redis as REDIS

def service_health_check():
    # print('##### Service Health Check #####')
    MASTER_INSTANCE_ID = str(uuid.uuid4()).split('-')[0]
    pass


def master_instance_picker():
    # print('##### Master Instance Picker #####')
    # Check if master instance has picked.
    r = REDIS.connectRedisSystemInfo()
    curent_master_instacne_id = r.get('MASTER_INSTANCE_ID')
    # print(curent_master_instacne_id)
    if curent_master_instacne_id == None:
        print('Master has not set. Set Master')
        r.set('MASTER_INSTANCE_ID', INSTANCE_ID)
    else:
        # print('Check if master instance is working.')
        # SERVICE_HEALTH_CHECK_URL

        # 
        # If master instance is not working properly. Pick a new instance
        pass

# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way. 
@util.close_old_connections
def delete_old_job_executions():
    print('##### Delete Old Logs #####')
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time(in seconds) to retain historical job execution records.
                    Defaults to 7 days.
    """

    execution_history_delete_policy = {
        'eva_delta_T_forecast' : 7200, # 2 hours
        'delete_old_job_executions': 86400 # 1 day
    }

    for job_id in execution_history_delete_policy:
        DjangoJobExecution.objects.filter(job_id__id=job_id).filter(run_time__lte=timezone.now() - timedelta(seconds=execution_history_delete_policy[job_id])).delete()
        