from datetime import datetime

from django.utils import timezone

# check if an object has already expired
def is_object_expired(obj, duration):
	expired_on = timezone.make_aware(datetime.now() - duration)
	return obj.timestamp < expired_on