from django.db import models

from bank_account.models import BankAccount
# Create your models here.


class FundType(models.Model):
	name 				= models.CharField(max_length=32)
	description			= models.TextField()

	def __str__(self):
		return self.name

class Fund(models.Model):
	account 			= models.ForeignKey(BankAccount, related_name='account_funds', on_delete=models.CASCADE, null=True)
	name 				= models.CharField(max_length=32)
	description 		= models.TextField()
	amount				= models.IntegerField()
	category			= models.ForeignKey(FundType, related_name='fund_category', on_delete=models.CASCADE, null=True)
	timestamp			= models.DateTimeField(auto_now_add=True, null=True)

	def __str__(self):
		return self.name

	def transfer(self, other_fund, amount):
		assert isinstance(other_fund, Fund)

		if self.amount < amount:
			raise ValidationError(f'{self.name} has insufficient balance.\nBalance: {self.amount}')
		other_fund.deposit(self.withdraw(amount))

	def deposit(self, amount):
		assert amount > 0
		self.amount += amount
		# save the changes to the database
		self.save()

	def withdraw(self, amount):
		assert amount > 0 and amount < self.amount 
		self.amount -= amount
		# save the changes to the database
		self.save()
		return amount

# model to store fund transfer history
class FundTransferHistory(models.Model):
	sender_fund 		= models.ForeignKey(Fund, related_name='send_to', on_delete=models.CASCADE)
	recipient_fund		= models.ForeignKey(Fund, related_name='receive_from', on_delete=models.CASCADE)
	amount 				= models.IntegerField()
	description 		= models.TextField()
	timestamp			= models.DateTimeField(auto_now_add=True, null=True)

	def __str__(self):
		return f'{self.sender_fund} to {self.recipient_fund}'