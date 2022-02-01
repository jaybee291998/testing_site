from datetime import date, datetime, timedelta
import random

from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy

from django.conf import settings

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView


from .models import Income, IncomeType
from .forms import IncomeAddForm

from accounts.utils import is_object_expired
from expenses.forms import DateSelectorForm
from expenses.views import EITBaseCreateView, EITBaseDetailView, EITBaseListView, EITBaseUpdateView, EITBaseDeleteView

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IncomeCreateView(CreateView):
	model = Income
	template_name = 'income/create.html'
	success_url = reverse_lazy('incomes_list')
	form_class = IncomeAddForm

	# method that vali
	def form_valid(self, form):
		bank_account = self.request.user.bank_account
		form.instance.account = bank_account

		# add the income to the bank account
		bank_account.balance += form.instance.amount
		# save the changes to the database
		bank_account.save()
		return super(IncomeCreateView, self).form_valid(form)

	def get_form_kwargs(self):
		kwargs = super(IncomeCreateView, self).get_form_kwargs()
		# a flag if the form is being to update
		kwargs.update({'prev_instance':None})
		kwargs.update({'account':self.request.user.bank_account})
		return kwargs


@method_decorator(login_required, name='dispatch')
class IncomeListView(ListView):
	model = Income
	template_name = 'income/list.html'
	context_object_name = 'incomes'
	paginate_by = 50

	def get_queryset(self):
		entry_date = date.today()

		if self.request.GET:
			entry_date = datetime.strptime(self.request.GET['date'][:10].replace('-',''), "%Y%m%d").date()
		# only get month and year of the entry date
		# in effect only the income for the month will be queried
		queryset = Income.objects.filter(account=self.request.user.bank_account, timestamp__year=entry_date.year, timestamp__month=entry_date.month).order_by('-timestamp')
		return queryset

	def get_context_data(self, **kwargs):
		context = super(IncomeListView, self).get_context_data(**kwargs)
		incomes = self.get_queryset()
		page = self.request.GET.get('page')
		paginator = Paginator(incomes, self.paginate_by)

		incomes = context['incomes']
		detail_links = [reverse_lazy('income_detail', kwargs={'pk':income.pk}) for income in incomes]
		total_income = sum([income.amount for income in incomes])
		entry_date = datetime.strptime(self.request.GET['date'][:10].replace('-',''), "%Y%m%d").date() if self.request.GET else date.today()

		try:
			incomes = paginator.page(page)
		except PageNotAnInteger:
			incomes = paginator.page(1)
		except EmptyPage:
			incomes = paginator.page(paginator.num_pages)
		context['income_details'] = zip(incomes, detail_links)
		context['add_income_link'] = reverse_lazy('income_create')
		context['go_home_link'] = reverse_lazy('home')
		context['total_income'] = total_income
		context['entry_date'] = entry_date
		context['form'] = DateSelectorForm()
		return context

@method_decorator(login_required, name='dispatch')
class IncomeDetailView(DetailView):
	model = Income
	template_name = 'income/detail.html'
	context_object_name = 'income'

	def get_object(self, queryset=None):
		obj = super(IncomeDetailView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(IncomeDetailView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

	def get_context_data(self, **kwargs):
		context = super(IncomeDetailView, self).get_context_data(**kwargs)
		income = context['income']
		delete_link = reverse_lazy('income_delete', kwargs={'pk':income.pk})
		update_link = reverse_lazy('income_update', kwargs={'pk':income.pk})
		# check if the object is already expired
		if not is_object_expired(income, settings.TWELVE_HOUR_DURATION):
			context['update_link'] = update_link
			context['delete_link'] = delete_link
			context['is_expired'] = False
		else:
			context['is_expired'] = True
		context['go_back_link'] = reverse_lazy('incomes_list')
		return context


@method_decorator(login_required, name='dispatch')
class IncomeUpdateView(UpdateView):
	model = Income
	template_name = 'income/update.html'
	context_object_name = 'income'
	form_class = IncomeAddForm

	def __init__(self, **kwargs):
		super(IncomeUpdateView, self).__init__(**kwargs)
		self.prev_instance = None

	# run custom code while the form is being validated
	def form_valid(self, form):
		# the amount to be updated
		prev_amount = self.prev_instance.amount
		# the amount that will replace the prev amount
		current_amount = form.instance.amount

		# the bank account
		bank_account = self.request.user.bank_account

		# the income is increased
		if prev_amount < current_amount:
			# add the increase to the unallocated balance
			bank_account.balance += (current_amount - prev_amount)
		else:
			if (prev_amount - current_amount) <= bank_account.balance:
				# the income is reduced, so subtract the amount that is reduced
				bank_account.balance -= (prev_amount - current_amount)
		# save the changes in the bank account
		bank_account.save()
		self.object = form.save()
		return super(IncomeUpdateView, self).form_valid(form)

	def get_success_url(self):
		return reverse_lazy('income_detail', kwargs={'pk':self.object.id})

	def get_object(self, queryset=None):
		obj = super(IncomeUpdateView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		self.prev_instance = Income.objects.get(pk=obj.id)
		return obj

	def get_queryset(self):
		queryset = super(IncomeUpdateView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

	# add additional custom data to the form arguments
	def get_form_kwargs(self):
		kwargs = super(IncomeUpdateView, self).get_form_kwargs()
		# a flag if the form is being to update
		# pass the previus instance of the object to the form
		kwargs.update({'prev_instance':self.prev_instance})
		# pass the bank account 
		kwargs.update({'account':self.request.user.bank_account})
		return kwargs

@method_decorator(login_required, name='dispatch')
class IncomeDeleteView(DeleteView):
	model = Income
	template_name = 'income/delete.html'
	success_url = reverse_lazy('incomes_list')

	def get_object(self, queryset=None):
		obj = super(IncomeDeleteView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		# if the income to be deleted is higher than the unallocated balance of the
		# bank account, dont allow deletion because the income will be subtracted to the balance
		# when that happens the balance will be negative
		# this only happens if the income is already allocated to a fund
		if obj.amount > self.request.user.bank_account.balance:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(IncomeDeleteView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

# views for the income type

# views for expense type

@method_decorator(login_required, name='dispatch')
class IncomeTypeCreateView(EITBaseCreateView):
	model = IncomeType
	template_name = 'income_type/create.html'
	success_url = reverse_lazy('income_types_list')

@method_decorator(login_required, name='dispatch')
class IncomeTypeListView(EITBaseListView):
	model = IncomeType
	template_name = 'income_type/list.html'
	context_object_name = 'income_types'
	detail_url_name = 'income_type_detail'
	add_object_url_name = 'income_type_create'

@method_decorator(login_required, name='dispatch')
class IncomeTypeDetailView(EITBaseDetailView):
	model = IncomeType
	template_name = 'income_type/detail.html'
	context_object_name = 'income_type'
	delete_url_name = 'income_type_delete'
	update_url_name = 'income_type_update'
	go_back_url_name = 'income_types_list'

	def get_context_data(self, **kwargs):
		context = super(IncomeTypeDetailView, self).get_context_data(**kwargs)
		income_type = context[self.context_object_name]
		context['is_expired'] = False
		if income_type.income.exists():
			context['is_expired'] = True
		return context

@method_decorator(login_required, name='dispatch')
class IncomeTypeUpdateView(EITBaseUpdateView):
	model = IncomeType
	template_name = 'income_type/update.html'
	context_object_name = 'income_type'
	fields = ( 'name' ,'description')
	go_back_url_name = 'income_type_detail'

	def get_object(self, queryset=None):
		obj = super(IncomeTypeUpdateView, self).get_object(queryset=queryset)
		if obj.income.exists():
			raise Http404()
		return obj


@method_decorator(login_required, name='dispatch')
class IncomeTypeDeleteView(EITBaseDeleteView):
	model = IncomeType
	template_name = 'income_type/delete.html'
	success_url = reverse_lazy('income_types_list')

	def get_object(self, queryset=None):
		obj = super(IncomeTypeDeleteView, self).get_object(queryset=queryset)
		if obj.income.exists():
			raise Http404()
		return obj
