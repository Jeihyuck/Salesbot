from django.apps import AppConfig

class alphaSchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.__apscheduler'
    verbose_name = 'Alpha Django AP Scheduler'
    def ready(self):    
        # print("start Scheduler....")
        from apps.__apscheduler import scheduler
        # scheduler.start()
