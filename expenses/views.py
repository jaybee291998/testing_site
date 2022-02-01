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

from rest_framework.parsers import JSONParser
from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework import generics

from .forms import ExpenseAddForm
from .models import Expense, Fund, ExpenseType
from .serializers import ExpenseSerializer
from .permissions import OwnerAndSuperUserOnly


from accounts.utils import is_object_expired
from .forms import DateSelectorForm

from .serializers import ExpenseSerializer

# Create your views here.
@method_decorator(login_required, name='dispatch')
class ExpenseCreateView(CreateView):
	model = Expense
	template_name = 'expenses/create.html'
	success_url = reverse_lazy('expenses_list')
	form_class = ExpenseAddForm

	def form_valid(self, form):
		form.instance.account = self.request.user.bank_account

		# get the fund to subtract from
		fund = form.instance.fund
		price = form.instance.price

		# subtract the price from the fund
		fund.amount -= price
		fund.save()

		return super(ExpenseCreateView, self).form_valid(form)

	def get_form_kwargs(self):
		kwargs = super(ExpenseCreateView, self).get_form_kwargs()
		kwargs.update({'account':self.request.user.bank_account})
		# a flag if the form is being to update
		kwargs.update({'prev_instance':None})
		return kwargs

@method_decorator(login_required, name='dispatch')
class ExpenseListView(ListView):
	model = Expense
	template_name = 'expenses/list.html'
	context_object_name = 'expenses'
	paginate_by = 20

	def get_queryset(self):
		entry_date = date.today()

		if self.request.GET:
			entry_date = datetime.strptime(self.request.GET['date'][:10].replace('-',''), "%Y%m%d").date()

		queryset = Expense.objects.filter(account=self.request.user.bank_account, timestamp__year=entry_date.year, timestamp__month=entry_date.month, timestamp__day=entry_date.day).order_by('-timestamp')
		return queryset

	def get_context_data(self, **kwargs):
		context = super(ExpenseListView, self).get_context_data(**kwargs)
		expenses = self.get_queryset()
		page = self.request.GET.get('page')
		paginator = Paginator(expenses, self.paginate_by)

		expenses = context['expenses']
		detail_links = [reverse_lazy('expenses_detail', kwargs={'pk':expense.pk}) for expense in expenses]
		total_expenditure = sum([expense.price for expense in expenses])
		entry_date = datetime.strptime(self.request.GET['date'][:10].replace('-',''), "%Y%m%d").date() if self.request.GET else date.today()

		try:
			expenses = paginator.page(page)
		except PageNotAnInteger:
			expenses = paginator.page(1)
		except EmptyPage:
			expenses = paginator.page(paginator.num_pages)
		context['expenses_details'] = zip(expenses, detail_links)
		context['add_expense_link'] = reverse_lazy('expenses_create')
		context['stats_link']  = reverse_lazy('get_stats_view')
		context['go_home_link'] = reverse_lazy('home')
		context['total_expenditure'] = total_expenditure
		context['entry_date'] = entry_date
		context['form'] = DateSelectorForm()
		return context

@method_decorator(login_required, name='dispatch')
class ExpenseDetailView(DetailView):
	model = Expense
	template_name = 'expenses/detail.html'
	context_object_name = 'expense'

	def get_object(self, queryset=None):
		obj = super(ExpenseDetailView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseDetailView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

	def get_context_data(self, **kwargs):
		context = super(ExpenseDetailView, self).get_context_data(**kwargs)
		expense = context['expense']
		delete_link = reverse_lazy('expenses_delete', kwargs={'pk':expense.pk})
		update_link = reverse_lazy('expenses_update', kwargs={'pk':expense.pk})
		# check if the object is already expired
		if not is_object_expired(expense, settings.TWELVE_HOUR_DURATION):
			context['update_link'] = update_link
			context['delete_link'] = delete_link
			context['is_expired'] = False
		else:
			context['is_expired'] = True

		context['go_back_link'] = reverse_lazy('expenses_list')
		return context


@method_decorator(login_required, name='dispatch')
class ExpenseUpdateView(UpdateView):
	model = Expense
	template_name = 'expenses/update.html'
	context_object_name = 'expenses'
	form_class = ExpenseAddForm

	def get_success_url(self):
		return reverse_lazy('expenses_detail', kwargs={'pk':self.object.id})

	def get_object(self, queryset=None):
		obj = super(ExpenseUpdateView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseUpdateView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

	def form_valid(self, form):
		price = form.instance.price
		fund = form.instance.fund

		prev_instance = Expense.objects.get(pk=self.object.pk)
		prev_price = prev_instance.price
		prev_fund = prev_instance.fund

		if fund == prev_fund:
			if price < prev_price:
				# since the current price is lower than the previous price
				# add the remaining back to the fund
				fund.amount += prev_price - price
			else:
				# subtract the excess from the fund
				fund.amount -= price - prev_price
		else:
			# add the previous price from the previous fund
			prev_fund.amount += prev_price

			# save the prev fund
			prev_fund.save()

			# subtract the current price to the current fund
			fund.amount -= price

		# save the fund instance
		fund.save()

		self.object = form.save()
		return super(ExpenseUpdateView, self).form_valid(form)

	# add additional custom data to the form arguments
	def get_form_kwargs(self):
		kwargs = super(ExpenseUpdateView, self).get_form_kwargs()
		kwargs.update({'account':self.request.user.bank_account})

		# a flag if the form is being to update
		kwargs.update({'prev_instance':Expense.objects.get(pk=self.object.id)})
		return kwargs


@method_decorator(login_required, name='dispatch')
class ExpenseDeleteView(DeleteView):
	model = Expense
	template_name = 'expenses/delete.html'
	success_url = reverse_lazy('expenses_list')

	def get_object(self, queryset=None):
		obj = super(ExpenseDeleteView, self).get_object(queryset=queryset)
		if obj.account != self.request.user.bank_account:
			raise Http404()
		if is_object_expired(obj, settings.TWELVE_HOUR_DURATION):
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseDeleteView, self).get_queryset()
		return queryset.filter(account=self.request.user.bank_account)

# base class for the expense type and income
# ExpenseIncomeTypeBase Class
@method_decorator(login_required, name='dispatch')
class EITBaseCreateView(CreateView):
	fields = ('name', 'description')

	def form_valid(self, form):
		form.instance.account = self.request.user.bank_account
		return super(EITBaseCreateView, self).form_valid(form)

@method_decorator(login_required, name='dispatch')
class EITBaseListView(ListView):
	detail_url_name = None
	add_object_url_name = None
	def get_queryset(self):
		queryset = self.model.objects.filter(account=self.request.user.bank_account)
		return queryset

	def get_context_data(self, **kwargs):
		context = super(EITBaseListView, self).get_context_data(**kwargs)

		context_objects = context[self.context_object_name]
		
		detail_links = [reverse_lazy(self.detail_url_name, kwargs={'pk':context_object.pk}) for context_object in context_objects]
		context['context_object_details'] = zip(context_objects, detail_links)
		context['add_object_link'] = reverse_lazy(self.add_object_url_name)
		context['go_home_link'] = reverse_lazy('home')
		return context

@method_decorator(login_required, name='dispatch')
class EITBaseDetailView(DetailView):
	delete_url_name = None
	update_url_name = None
	go_back_url_name = None

	def get_object(self, queryset=None):
		pk = self.kwargs.get(self.pk_url_kwarg)
		if pk is None:
			raise AttributeError("Generic Delete view must be called with a PK")
		try:
			obj = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			raise Http404("You suck")

		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj

	def get_context_data(self, **kwargs):
		context = super(EITBaseDetailView, self).get_context_data(**kwargs)
		context_object = context[self.context_object_name]
		context['delete_link'] = reverse_lazy(self.delete_url_name, kwargs={'pk':context_object.pk})
		context['update_link'] = reverse_lazy(self.update_url_name, kwargs={'pk':context_object.pk})
		context['go_back_link'] = reverse_lazy(self.go_back_url_name)
		return context

@method_decorator(login_required, name='dispatch')
class EITBaseUpdateView(UpdateView):
	go_back_url_name = None
	fields = ( 'name' ,'description')

	def get_success_url(self):
		return reverse_lazy(self.go_back_url_name, kwargs={'pk':self.object.id})

	def get_object(self, queryset=None):
		pk = self.kwargs.get(self.pk_url_kwarg)
		if pk is None:
			raise AttributeError("Generic Update view must be called with a PK")
		try:
			obj = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			raise Http404("You suck")
		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj


@method_decorator(login_required, name='dispatch')
class EITBaseDeleteView(DeleteView):
	def get_object(self, queryset=None):
		pk = self.kwargs.get(self.pk_url_kwarg)
		if pk is None:
			raise AttributeError("Generic Delete view must be called with a PK")
		try:
			obj = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			raise Http404("You suck")

		if obj.account != self.request.user.bank_account:
			raise Http404()
		return obj

# views for expense type

@method_decorator(login_required, name='dispatch')
class ExpenseTypeCreateView(EITBaseCreateView):
	model = ExpenseType
	template_name = 'expense_type/create.html'
	success_url = reverse_lazy('expense_types_list')

@method_decorator(login_required, name='dispatch')
class ExpenseTypeListView(EITBaseListView):
	model = ExpenseType
	template_name = 'expense_type/list.html'
	context_object_name = 'expense_types'
	detail_url_name = 'expense_type_detail'
	add_object_url_name = 'expense_type_create'

@method_decorator(login_required, name='dispatch')
class ExpenseTypeDetailView(EITBaseDetailView):
	model = ExpenseType
	template_name = 'expense_type/detail.html'
	context_object_name = 'expense_type'
	delete_url_name = 'expense_type_delete'
	update_url_name = 'expense_type_update'
	go_back_url_name = 'expense_types_list'

	def get_context_data(self, **kwargs):
		context = super(ExpenseTypeDetailView, self).get_context_data(**kwargs)
		expense_type = context[self.context_object_name]
		context['is_expired'] = False
		if expense_type.expense.exists():
			context['is_expired'] = True
		return context

@method_decorator(login_required, name='dispatch')
class ExpenseTypeUpdateView(EITBaseUpdateView):
	model = ExpenseType
	template_name = 'expense_type/update.html'
	context_object_name = 'expense_type'
	fields = ( 'name' ,'description')
	go_back_url_name = 'expense_type_detail'

	def get_object(self, queryset=None):
		obj = super(ExpenseTypeUpdateView, self).get_object(queryset=queryset)
		if obj.expense.exists():
			raise Http404()
		return obj


@method_decorator(login_required, name='dispatch')
class ExpenseTypeDeleteView(EITBaseDeleteView):
	model = ExpenseType
	template_name = 'expense_type/delete.html'
	success_url = reverse_lazy('expense_types_list')

	def get_object(self, queryset=None):
		obj = super(ExpenseTypeDeleteView, self).get_object(queryset=queryset)
		if obj.expense.exists():
			raise Http404()
		return obj


@method_decorator(login_required, name='dispatch')
class ExpenseList(APIView):

	def get(self, request, format=None):
		expenses = Expense.objects.filter(account=request.user.bank_account)
		serializer = ExpenseSerializer(expenses, many=True)
		return Response(serializer.data)

	def post(self, request, format=None):
		serializer = ExpenseSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save(account=request.user.bank_account)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(login_required, name='dispatch')
class ExpenseDetail(APIView):

	permission_classes = [OwnerAndSuperUserOnly]

	def get_object(self, pk):
		try:
			expense = Expense.objects.get(pk=pk)
			if expense.account != self.request.user.bank_account and not self.request.user.is_superuser: raise Http404()
			return expense
		except Expense.DoesNotExist:
			raise Http404()

	def get(self, request, pk, format=None):
		expense = self.get_object(pk)
		serializer = ExpenseSerializer(expense)
		return Response(serializer.data)

	def put(self, request, pk, format=None):
		expense = self.get_object(pk)
		serializer = ExpenseSerializer(expense, data=request.data)
		if serializer.is_valid():
			serializer.save(account=request.user.bank_account)
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk, format=None):
		expense = self.get_object(pk)
		expense.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

@login_required
def get_stats(request):
	given_interval = None 
	one_week_interval = timedelta(days=7)
	one_month_interval = timedelta(days=31)
	three_month_interval = timedelta(days=93)
	interval = one_week_interval 
	if request.method == 'GET':
		given_interval = request.GET.get('interval');
		if given_interval == 'WEEK': interval = one_week_interval
		elif given_interval == 'MONTH': interval = one_month_interval
		elif given_interval == 'THREEMONTHS': interval = three_month_interval
	
	end_date = date.today() + timedelta(days=1)
	start_date = end_date - interval
	expenses = Expense.objects.filter(account=request.user.bank_account, timestamp__range=[start_date, end_date])
	serializer = ExpenseSerializer(expenses, many=True)
	# dictionary that contains the id of the fund as key
	# and the name of the fund as a value
	fund_names = {}
	for fund in Fund.objects.filter(account=request.user.bank_account):
		fund_names[fund.id] = fund.name

	# dictionary that conatains the id of expense types as key
	# and expense type name as value
	category_names = {}
	for expense_type in ExpenseType.objects.filter(account=request.user.bank_account):
		category_names[expense_type.id] = expense_type.name

	data = {
		'expense_data': serializer.data,
		'fund_names': fund_names,
		'category_names': category_names,
	}
	return JsonResponse(data, safe=False)

@login_required
def get_stats_view(request):
	context = {
		'domain': reverse_lazy('get_stats'),
		'form': DateSelectorForm()
	}
	return render(request, 'expenses/get_stats_view.html', context)

