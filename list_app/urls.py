from django.urls import path
from . import views
urlpatterns = [
	path('list-api/', views.ListList.as_view(), name='listlist-api'),
	path('detail-api/<int:pk>/', views.ListDetail.as_view(), name='listdetail-api'),
	path('list/', views.list_app_view, name='list_app'),
]