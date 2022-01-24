from django.shortcuts import render, redirect
from .forms import UserLoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy

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