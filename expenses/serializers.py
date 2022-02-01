from rest_framework import serializers
from .models import Expense, ExpenseType

class ExpenseSerializer(serializers.ModelSerializer):
	class Meta:
		model = Expense
		fields = ['id', 'description', 'category', 'price', 'timestamp', 'fund', 'account']

class ExpenseTypeSerializer(serializers.ModelSerializer):
	model = ExpenseType
	fields = ['id', 'name', 'description', 'account']