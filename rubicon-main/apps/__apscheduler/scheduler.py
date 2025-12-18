from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from apscheduler.triggers.cron import CronTrigger
from alpha.settings import RUN_APSCHEDULER
import apps.__apscheduler.__job._00_basic as scheduledJobBasic
import apps.__apscheduler.__job._01_ht as scheduledJobHT

RUN_APSCHEDULER = False

if RUN_APSCHEDULER:
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        scheduledJobBasic.delete_old_job_executions,
        trigger=CronTrigger.from_crontab('0 0 * * *'),  # Midnight on Monday, before start of the next work week.
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )

    #########################################################################

    scheduler.add_job(
        scheduledJobHT.eva_delta_T_forecast,
        trigger=CronTrigger(
            second="*/10"
        ),  # Every 10 secondes
        id="eva_delta_T_forecast",
        max_instances=1,
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()

# https://crontab.guru/examples.html
# minute, hour, day, month, day

 
# **Expression**	**Meaning**
# 0 0 12 * * ?	Fire at 12pm (noon) every day
# 0 15 10 ? * *	Fire at 10:15am every day
# 0 15 10 * * ?	Fire at 10:15am every day
# 0 15 10 * * ? *	Fire at 10:15am every day
# 0 15 10 * * ? 2005	Fire at 10:15am every day during the year 2005
# 0 * 14 * * ?	Fire every minute starting at 2pm and ending at 2:59pm, every day
# 0 0/5 14 * * ?	Fire every 5 minutes starting at 2pm and ending at 2:55pm, every day
# 0 0/5 14,18 * * ?	Fire every 5 minutes starting at 2pm and ending at 2:55pm, AND fire every 5 minutes starting at 6pm and ending at 6:55pm, every day
# 0 0-5 14 * * ?	Fire every minute starting at 2pm and ending at 2:05pm, every day
# 0 10,44 14 ? 3 WED	Fire at 2:10pm and at 2:44pm every Wednesday in the month of March.
# 0 15 10 ? * MON-FRI	Fire at 10:15am every Monday, Tuesday, Wednesday, Thursday and Friday
# 0 15 10 15 * ?	Fire at 10:15am on the 15th day of every month
# 0 15 10 L * ?	Fire at 10:15am on the last day of every month
# 0 15 10 L-2 * ?	Fire at 10:15am on the 2nd-to-last last day of every month
# 0 15 10 ? * 6L	Fire at 10:15am on the last Friday of every month
# 0 15 10 ? * 6L	Fire at 10:15am on the last Friday of every month
# 0 15 10 ? * 6L 2002-2005	Fire at 10:15am on every last friday of every month during the years 2002, 2003, 2004 and 2005
# 0 15 10 ? * 6#3	Fire at 10:15am on the third Friday of every month
# 0 0 12 1/5 * ?	Fire at 12pm (noon) every 5 days every month, starting on the first day of the month.
# 0 11 11 11 11 ?	Fire every November 11th at 11:11am.