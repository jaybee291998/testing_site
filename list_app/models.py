from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.
class List(models.Model):
	user 			= models.ForeignKey(User, related_name='my_list', on_delete=models.CASCADE)
	name 			= models.CharField(max_length=64)
	content			= models.TextField()
	timestamp 		= models.DateTimeField(auto_now_add=True)
	last_modified	= models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name