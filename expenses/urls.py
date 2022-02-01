from django.urls import path, include
from . import views

urlpatterns = [
    path('list/', views.ExpenseListView.as_view(), name='expenses_list'),
    path('create/', views.ExpenseCreateView.as_view(), name='expenses_create'),
    path('detail/<int:pk>', views.ExpenseDetailView.as_view(), name='expenses_detail'),
    path('update/<int:pk>', views.ExpenseUpdateView.as_view(), name='expenses_update'),
    path('delete/<int:pk>', views.ExpenseDeleteView.as_view(), name='expenses_delete'),

    path('et-list/', views.ExpenseTypeListView.as_view(), name='expense_types_list'),
    path('et-create/', views.ExpenseTypeCreateView.as_view(), name='expense_type_create'),
    path('et-detail/<int:pk>', views.ExpenseTypeDetailView.as_view(), name='expense_type_detail'),
    path('et-update/<int:pk>', views.ExpenseTypeUpdateView.as_view(), name='expense_type_update'),
    path('et-delete/<int:pk>', views.ExpenseTypeDeleteView.as_view(), name='expense_type_delete'),

    path('expenses_list_api/', views.ExpenseList.as_view(), name='expenses_list_api'),
    path('expenses_detail_api/<int:pk>', views.ExpenseDetail().as_view(), name='expenses_detail_api'),
    path('api_auth/', include('rest_framework.urls')),
    path('get_stats/', views.get_stats, name='get_stats'),
    path('get_stats_view/', views.get_stats_view, name='get_stats_view')
]
