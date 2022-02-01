from django.urls import path, include
from . import views

urlpatterns = [
    path('list/', views.IncomeListView.as_view(), name='incomes_list'),
    path('create/', views.IncomeCreateView.as_view(), name='income_create'),
    path('detail/<int:pk>', views.IncomeDetailView.as_view(), name='income_detail'),
    path('update/<int:pk>', views.IncomeUpdateView.as_view(), name='income_update'),
    path('delete/<int:pk>', views.IncomeDeleteView.as_view(), name='income_delete'),

    path('it-list/', views.IncomeTypeListView.as_view(), name='income_types_list'),
    path('it-create/', views.IncomeTypeCreateView.as_view(), name='income_type_create'),
    path('it-detail/<int:pk>', views.IncomeTypeDetailView.as_view(), name='income_type_detail'),
    path('it-update/<int:pk>', views.IncomeTypeUpdateView.as_view(), name='income_type_update'),
    path('it-delete/<int:pk>', views.IncomeTypeDeleteView.as_view(), name='income_type_delete')
]
