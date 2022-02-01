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

from rest_framework.parsers import JSONParser
from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics

from .forms import ExpenseAddForm
from .models import Expense, Fund
from .serializers import ExpenseSerializer
from .permissions import OwnerAndSuperUserOnly



from .forms import DateSelectorForm
# Create your views here.
@method_decorator(login_required, name='dispatch')
class ExpenseCreateView(CreateView):
	model = Expense
	template_name = 'expenses/create.html'
	success_url = reverse_lazy('expenses_list')
	form_class = ExpenseAddForm

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super(ExpenseCreateView, self).form_valid(form)

	def get_form_kwargs(self):
		kwargs = super(ExpenseCreateView, self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

@method_decorator(login_required, name='dispatch')
class ExpenseListView(ListView):
	model = Expense
	template_name = 'expenses/list.html'
	context_object_name = 'expenses'
	paginate_by = 10

	def get_queryset(self):
		entry_date = date.today()

		if self.request.GET:
			entry_date = datetime.strptime(self.request.GET['date'][:10].replace('-',''), "%Y%m%d").date()

		queryset = Expense.objects.filter(user=self.request.user, timestamp__year=entry_date.year, timestamp__month=entry_date.month, timestamp__day=entry_date.day).order_by('-timestamp')
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
		if obj.user != self.request.user:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseDetailView, self).get_queryset()
		return queryset.filter(user=self.request.user)

	def get_context_data(self, **kwargs):
		context = super(ExpenseDetailView, self).get_context_data(**kwargs)
		expense = context['expense']
		delete_link = reverse_lazy('expenses_delete', kwargs={'pk':expense.pk})
		update_link = reverse_lazy('expenses_update', kwargs={'pk':expense.pk})
		context['delete_link'] = delete_link
		context['update_link'] = update_link
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
		if obj.user != self.request.user:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseUpdateView, self).get_queryset()
		return queryset.filter(user=self.request.user)

	def get_form_kwargs(self):
		kwargs = super(ExpenseUpdateView, self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

@method_decorator(login_required, name='dispatch')
class ExpenseDeleteView(DeleteView):
	model = Expense
	template_name = 'expenses/delete.html'
	success_url = reverse_lazy('expenses_list')

	def get_object(self, queryset=None):
		obj = super(ExpenseDeleteView, self).get_object(queryset=queryset)
		if obj.user != self.request.user:
			raise Http404()
		return obj

	def get_queryset(self):
		queryset = super(ExpenseDeleteView, self).get_queryset()
		return queryset.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ExpenseList(APIView):

	def get(self, request, format=None):
		expenses = Expense.objects.filter(user=request.user)
		serializer = ExpenseSerializer(expenses, many=True)
		return Response(serializer.data)

	def post(self, request, format=None):
		serializer = ExpenseSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save(user=request.user)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def perform_create(self, serializer):
		serializer.save(user=request.user)

@method_decorator(login_required, name='dispatch')
class ExpenseDetail(APIView):

	permission_classes = [OwnerAndSuperUserOnly]

	def get_object(self, pk):
		try:
			expense = Expense.objects.get(pk=pk)
			if expense.user != self.request.user and not self.request.user.is_superuser: raise Http404()
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
			serializer.save(user=request.user)
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
	expenses = Expense.objects.filter(user=request.user, timestamp__range=[start_date, end_date])
	data = {
		'data': [expense.price for expense in expenses],
		'labels': [expense.timestamp.day for expense in expenses],
		'interval': given_interval
	}
	return JsonResponse(data, safe=False)

@login_required
def get_stats_view(request):
	context = {
		'domain': reverse_lazy('get_stats'),
		'form': DateSelectorForm()
	}
	return render(request, 'expenses/get_stats_view.html', context)

