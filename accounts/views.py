from django.shortcuts import render, redirect
from .forms import UserLoginForm
from django.contrib.auth import authenticate, login, logout

from django.utils.decorators import method_decorator
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
		'form': form
	}
	return render(request, 'accounts/login.html', context)

def logout_view(request):
	logout(request)
	return redirect('login')

@login_required
def home_view(request):
	context = {
		'logout_link': reverse_lazy('logout'),
		'expense_home_link': reverse_lazy('expenses_list'),
		'income_home_link': reverse_lazy('incomes_list'),
		'diary_home_link': reverse_lazy('diary-list-api'),
		'fund_home_link': reverse_lazy('funds_list'),
		'list_home_link': reverse_lazy('lists_list'),
		'expense_type_link': reverse_lazy('expense_types_list'),
		'income_type_link': reverse_lazy('income_types_list')
	}
	return render(request, 'accounts/home.html', context)
