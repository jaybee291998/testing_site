from datetime import date, datetime, timedelta
import random

from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from django.conf import settings


from .models import Fund, FundTransferHistory
from .forms import FundAllocationForm, FundTransferForm

from expenses.forms import DateSelectorForm
from accounts.utils import is_object_expired

# Create your views here.
@method_decorator(login_required, name='dispatch')
class FundCreateView(CreateView):
	model = Fund
	template_name = 'fund/create.html'
	success_url = reverse_lazy('funds_list')
	fields = ('name', 'description', 'category')

	def form_valid(self, form):
		form.instance.account = self.request.user.bank_account
		form.instance.amount = 0
		return super(FundCreateView, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
class FundListView(ListView):
	model = Fund
	template_name = 'fund/list.html'
	context_object_name = 'funds'
	paginate_by = 10

	def get_queryset(self):
		queryset = Fund.objects.filter(account=self.request.user.bank_account)
		return queryset

	def get_context_data(self, **kwargs):
		context = super(FundListView, self).get_context_data(**kwargs)
		funds = self.get_queryset()

		# unallocated balance from the bank account
		# which means the money that is not on any funds
		unallocated_balance = self.request.user.bank_account.balance

		# total balance
		# are the remaining money from all the funds + the unallocated balance
		total_balance = unallocated_balance + sum([fund.amount for fund in funds])
		funds = context['funds']
		
		detail_links = [reverse_lazy('fund_detail', kwargs={'pk':fund.pk}) for fund in funds]
		context['fund_details'] = zip(funds, detail_links)
		context['add_fund_link'] = reverse_lazy('fund_create')
		context['go_home_link'] = reverse_lazy('home')
		context['unallocated_balance'] = unallocated_balance
		context['total_balance'] = total_balance
		return context

@method_decorator(login_required, name='dispatch')
class FundDetailView(DetailView):
	model = Fund
	template_name = 'fund/detail.html'
	context_object_name = 'fund'

	def get_object(self, queryset=None):
		obj = super(FundDetailView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(FundDetailView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

	def get_context_data(self, **kwargs):
		context = super(FundDetailView, self).get_context_data(**kwargs)
		fund = context['fund']
		delete_link = reverse_lazy('fund_delete', kwargs={'pk':fund.pk})
		update_link = reverse_lazy('fund_update', kwargs={'pk':fund.pk})
		# link to fund allocation page
		context['fund_allocation_link'] = reverse_lazy('fund_allocation', kwargs={'fund_id':fund.pk})
		context['fund_transfer_link'] = reverse_lazy('fund_transfer', kwargs={'fund_id':fund.pk})

		# check if the fund is expired, if it is remove the ability to update
		if not is_object_expired(fund, settings.TWELVE_HOUR_DURATION) and not fund.fund_expenses.exists(): 
			context['delete_link'] = delete_link
			context['update_link'] = update_link
			context['is_expired'] = False
		else:
			context['is_expired'] = True
		context['go_back_link'] = reverse_lazy('funds_list')
		return context


@method_decorator(login_required, name='dispatch')
class FundUpdateView(UpdateView):
	model = Fund
	template_name = 'fund/update.html'
	context_object_name = 'fund'
	fields = ( 'name' ,'description', 'category')

	def get_success_url(self):
		return reverse_lazy('fund_detail', kwargs={'pk':self.object.id})

	def get_object(self, queryset=None):
		obj = super(FundUpdateView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		if obj.fund_expenses.exists():
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(FundUpdateView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

@method_decorator(login_required, name='dispatch')
class FundDeleteView(DeleteView):
	model = Fund
	template_name = 'fund/delete.html'
	success_url = reverse_lazy('funds_list')

	def get_object(self, queryset=None):
		obj = super(FundDeleteView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		if obj.fund_expenses.exists():
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(FundDeleteView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

@login_required
def fund_allocation_view(request, fund_id, *args, **kwargs):
	try:
		fund = Fund.objects.get(pk=fund_id)
	except (TypeError, ValueError, OverflowError, Fund.DoesNotExist):
		fund = None

	amount = None
	action = None
	bank_account = request.user.bank_account
	errors = []
	if fund is not None:
		form = FundAllocationForm(request.POST or None)
		if fund.account.user == request.user:
			if form.is_valid():
				amount = form.cleaned_data.get('amount')
				action = form.cleaned_data.get('action')

				# allocate to fund
				if action=='AL':
					# check if the amount to allocate to the fund is 
					# less than the unallocated balnace of the bank account
					if amount < bank_account.balance:
						# add the amount to the fund
						fund.amount += amount
						# subtract the amount to the bank account balance
						bank_account.balance -= amount
					else:
						# trying to allocate an amount greater than the current balance
						errors.append(f'You can only allocate up to {bank_account.balance}, other wise your balance will be in the negative')
				# deallocate
				else:
					# check if the amount to deallocate is less than the remaining amount on the fund
					if amount <= fund.amount:
						# subtract the amount to the fund
						fund.amount -= amount
						# add the deallocated amount to the bank account balance
						bank_account.balance += amount
					else:
						# trying to deallocate an amount that is greater than the available to the fund
						errors.append(f'You cannot deallocate more than {fund.amount}, current {fund.name} balance {fund.amount}')
				# save the changes
				fund.save()
				bank_account.save()
				# if there are no errors
				if len(errors) == 0:
					# return to fund_detail
					return redirect('fund_detail', pk=fund.id)

	else:
		raise Http404()

	context = {
		'form': form,
		'errors': errors,
		'unallocated_balance': bank_account.balance,
		'fund_amount': fund.amount,
		'fund_name': fund.name
	}

	return render(request, 'fund/fund_allocation.html', context)

# transfer balance from an account to another account
@login_required
def transfer_FTF(request, fund_id, *args, **kwargs):
	try:
		fund = Fund.objects.get(id=fund_id)
	except (ValueError, OverflowError, TypeError, Fund.DoesNotExist):
		fund = None

	# check if the fund exists, then check if the logged in user is the owner of the fund
	if fund is not None and fund.account == request.user.bank_account:
		form = FundTransferForm(request.user.bank_account, fund, request.POST or None)
		if form.is_valid():
			description = form.cleaned_data.get('description')
			amount = form.cleaned_data.get('amount')
			recipient_fund = form.cleaned_data.get('recipient_fund')

			# tranfer the amount from the current fund to the recipient fund
			fund.transfer(recipient_fund, amount)

			# added the transaction to the history
			fund_history = FundTransferHistory(sender_fund=fund, recipient_fund=recipient_fund, amount=amount, description=description)
			fund_history.save()

			# return to the detail page of the fund
			return redirect('fund_detail', pk=fund.id)

	else:
		raise Http404()
	context = {
		'form': form,
		'fund': fund
	}

	return render(request, 'fund/fund_transfer.html', context)