from django.shortcuts import render

from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework import status, generics, permissions

from .permissions import IsOwner
from .models import List
from .serializer import ListSerializer
# Create your views here.
# @method_decorator(login_required, name='dispatch')
class ListList(generics.ListCreateAPIView):
	serializer_class = ListSerializer
	permission_classes = [permissions.IsAuthenticated]

	# override
	# override get_queryset so that only the users list will be retrieved
	def get_queryset(self):
		return self.request.user.my_list.all()

	# override the perform_create so that the user is saved
	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

class ListDetail(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = ListSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwner]
	# override get_queryset so that only the users list will be retrieved
	def get_queryset(self):
		return self.request.user.my_list.all()	

# view to serve the initial html doc for the list app
@login_required
def list_app_view(request):
	detail_link = reverse_lazy('listdetail-api', kwargs={'pk':0})
	context = {
		'list_api':reverse_lazy('listlist-api'),
		'detail_api':detail_link[0:len(detail_link)]
	}

	return render(request, 'list_app/list_app.html', context)
