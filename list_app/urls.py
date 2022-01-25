from django.urls import path
from . import views
urlpatterns = [
	path('list-api/', views.ListList.as_view(), name='listlist-api'),
	path('detail-api/', views.ListDetail.as_view(), name='listdetail-api'),
]