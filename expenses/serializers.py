from rest_framework import serializers
from .models import Expense, ExpenseType

class ExpenseSerializer(serializers.ModelSerializer):
	account 			= serializers.ReadOnlyField(source='account.username') 
	class Meta:
		model = Expense
		fields = ['id', 'description', 'category', 'price', 'timestamp', 'fund', 'account']

	def validate_price(self, value):
		"""
			check if the price provided is appropriate
		"""
		if value <= 0:
			raise serializers.ValidationError('Price cant be less than or equal to zero.')
		return value

	def validate(self, data):
		"""
			checks if the fund to be used has sufficient balance
		"""
		if data['price'] > data['fund'].amount:
			raise serializers.ValidationError('Fund {fund.name} has an insufficient balance.\nCurrent balance: {fund.amout}')
		return data;

	def create(self, validated_data):
		price = validated_data.get('price')
		fund = validated_data.get('fund')
		fund.withdraw(price)
		fund.save()
		return Expense.objects.create(**validated_data)

class ExpenseTypeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ExpenseType
		fields = ['id', 'name', 'description', 'account']