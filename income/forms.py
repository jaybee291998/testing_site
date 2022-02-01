from django import forms 
from .models import Income, IncomeType
from django.core.exceptions import ValidationError  

class IncomeAddForm(forms.ModelForm):

	# the income category should be based on the bank account of the user
	category = forms.ModelChoiceField(queryset=None, initial=0)

	def __init__(self, *args, **kwargs):
		self.prev_instance = kwargs.pop('prev_instance')
		self.bank_account = kwargs.pop('account')
		super(IncomeAddForm, self).__init__(*args, **kwargs)

		# set the queryset equal to the incometypes to the user
		self.fields["category"].queryset = IncomeType.objects.filter(account=self.bank_account)

	class Meta:
		model = Income
		fields = [
			'description',
			'category',
			'amount',
			'source'
		]

	def clean_amount(self):
		amount = self.cleaned_data['amount']
		# only accept positive integers
		if amount < 0:
			raise ValidationError('Negative Integers are not allowed')

		if self.prev_instance is not None:
			prev_amount = self.prev_instance.amount
			# if the prev_amount is reduced
			if amount < prev_amount:
				# if the amount reduced is greater than  the unallocated balance
				if (prev_amount - amount) > self.bank_account.balance:
					raise ValidationError(f'You cannot reduce this income lower than {prev_amount - self.bank_account.balance}, because if you any longer you will have negative balance')
		
		return amount
