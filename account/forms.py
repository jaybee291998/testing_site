from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class UserLoginForm(forms.Form):
	username 			= forms.CharField()
	password 			= forms.CharField()

	def clean_username(self):
		sub_cleaned_username = super().clean_username()

		if not User.objects.filter(username=sub_cleaned_username).exists():
			raise forms.ValidationError(f'User: {sub_cleaned_username} does not exists.')

		return sub_cleaned_username

	def clean_password(self):
		sub_cleaned_password = super().clean_password()
		username = self.clean_username()
		user = authenticate(username=username, password=sub_cleaned_password)

		if not user:
			raise forms.ValidationError("Inavalid Password")