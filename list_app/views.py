from django.shortcuts import render

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework import status, generics


from .models import List
from .serializer import ListSerializer
# Create your views here.
@method_decorator(login_required, name='dispatch')
class ListList(generics.ListCreateAPIView):
	serializer_class = ListSerializer

	# override
	# override get_queryset so that only the users list will be retrieved
	def get_queryset(self):
		return List.objects.filter(user=request.user)

	# override the perform_create so that the user is saved
	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

@method_decorator(login_required, name='dispatch')
class ListDetail(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = ListSerializer
	# override get_queryset so that only the users list will be retrieved
	def get_queryset(self):
		return self.request.user.my_list.all()	
