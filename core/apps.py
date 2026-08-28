from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

#    def ready(self):
#        # create default admin user if not exists
#        from django.contrib.auth import get_user_model
#        User = get_user_model()
#        if not User.objects.filter(roll_number='ADMIN').exists():
#            User.objects.create_superuser(roll_number='ADMIN', password='25m0005@iitb', username='admin', email='')
