from django.db import models
from django.contrib.auth import get_user_model

from bank_account.models import BankAccount
from fund.models import Fund
User = get_user_model()
# Create your models here.
class ExpenseType(models.Model):
	name 				= models.CharField(max_length=32)
	description			= models.TextField()
	account 			= models.ForeignKey(BankAccount, related_name='account_expense_type', on_delete=models.CASCADE, null=True)

	def __str__(self):
		return self.name

class Expense(models.Model):
	description 		= models.TextField()
	category 			= models.ForeignKey(ExpenseType, related_name='expense', on_delete=models.CASCADE, null=True)
	price				= models.IntegerField(default=0)
	timestamp			= models.DateTimeField(auto_now_add=True)
	fund 				= models.ForeignKey(Fund, related_name='fund_expenses', on_delete=models.CASCADE, null=True)
	account 			= models.ForeignKey(BankAccount, related_name='account_expenses', on_delete=models.CASCADE, null=True)

	def __str__(self):
		return self.description[:10] + ' - ' + str(self.category)

	def delete(self, *args, **kwargs):
		# add the price of the expense to be deleted
		# to the fund where it was subtracted before
		prc = self.price
		fnd = self.fund

		# add the amount that was subtracted before
		fnd.amount += prc
		fnd.save()

		super(Expense, self).delete(*args, **kwargs)