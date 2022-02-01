from django import forms 
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class UserLoginForm(forms.Form):
	username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'username', 'class':'form-control'}))
	password = password = forms.CharField(widget = forms.PasswordInput(attrs={'placeholder':'password', 'class':'form-control'}))

	def clean(self, *args, **kwargs):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		if not User.objects.filter(username=username).exists():
			raise forms.ValidationError(f'"{username}" does not exist')
		user = authenticate(username=username, password=password)
		if not user:
			raise forms.ValidationError("Invalid password")

		return super(UserLoginForm, self).clean(*args, **kwargs)
