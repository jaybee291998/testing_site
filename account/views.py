from django.shortcuts import render, redirect
from .forms import UserLoginForm, UserRegisterForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy

User = get_user_model()
# Create your views here.
def login_view(request):
	form = UserLoginForm(request.POST or None)
	if form.is_valid():
		username = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password')

		user = authenticate(username=username, password=password)
		login(request, user)
		return redirect('home')

	context = {
		'form':form
	}
	return render(request, 'account/login.html', context)

def register_view(request):
	form = UserRegisterForm(request.POST or None)
	if form.is_valid():
		username = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password')

		# create a user 
		user = User(username=username)
		# user the builtin function to save the password properly
		user.set_password(password)
		# save the user to the database
		user.save()

		return redirect('login')
	context = {
		'form':form
	}
	return render(request, 'account/register.html', context)


@login_required
def logout_view(request):
	logout(request)
	return redirect('login')

@login_required
def home_view(request):
	context = {
		'logout_link': reverse_lazy('logout'),
		'message': 'pussy'
	}
	return render(request, 'account/home.html', context)