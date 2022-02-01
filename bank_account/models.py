from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
# Create your models here.
class BankAccount(models.Model):
	user 			= models.OneToOneField(User, related_name='bank_account', on_delete=models.CASCADE)
	balance			= models.IntegerField()

	def __str__(self):
		return f'{self.user.username} - Bank Account'
