from django import forms
from django.core.exceptions import ValidationError
from .models import Fund

class FundAllocationForm(forms.Form):
	ACTIONS = (
		('AL', 'Allocate'),
		('DL', 'Deallocate'))

	amount 			= forms.IntegerField()
	action 			= forms.ChoiceField(choices=ACTIONS)

	def clean_amount(self):
		amount = self.cleaned_data['amount']

		if amount < 0:
			raise ValidationError("Amount cant be negative")

		return amount

class FundTransferForm(forms.Form):
	def __init__(self, account, current_fund, *args, **kwargs):
		queryset = Fund.objects.filter(account=account).exclude(pk=current_fund.id)
		self.current_fund = current_fund
		super(FundTransferForm, self).__init__(*args, **kwargs)
		self.fields['recipient_fund'].queryset = queryset

	description 		= forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Description', 'class':'form-control'}))	
	amount 				= forms.IntegerField()
	recipient_fund 		= forms.ModelChoiceField(queryset=None, initial=0)

	def clean_amount(self):
		amount = self.cleaned_data.get('amount')

		if amount < 0:
			raise ValidationError("No Negative amount.")
		if amount > self.current_fund.amount:
			raise ValidationError(f'You have insufficient amount to transfer.\nCurrent balance:{self.current_fund.amount}')

		return amount