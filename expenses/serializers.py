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
		print(self.instance)
		if data['price'] > data['fund'].amount:
			raise serializers.ValidationError('Fund {fund.name} has an insufficient balance.\nCurrent balance: {fund.amout}')
		return data;

	def create(self, validated_data):
		price = validated_data.get('price')
		fund = validated_data.get('fund')
		fund.withdraw(price)
		fund.save()
		return Expense.objects.create(**validated_data)

	def update(self, instance, validated_data):
		current_fund = validated_data.get('fund', instance.fund)
		prev_fund = instance.fund

		current_price = validated_data.get('price', instance.price)

		if current_fund != prev_fund:
			prev_price = instance.price

			# return the previous expense to the previous fund
			prev_fund.deposit(prev_price)

			# save the previous fund
			prev_fund.save()
		else:
			# decide how much to deposit back or withdraw
			if current_price > prev_price:
				# subtract the current price to the current fund
				current_fund.withdraw(current_price - prev_price)
			else:
				# since the price is equal or lowered deposit back the difference
				current_fund.deposit(prev_price - current_price)
			# save the current fund
			current_fund.save()

		instance.description = validated_data.get('description', instance.description)
		instance.category = validated_data.get('category', instance.category)
		instance.price = validated_data.get('price', instance.price)
		instance.fund = current_fund
		instance.save()
		return instance


class ExpenseTypeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ExpenseType
		fields = ['id', 'name', 'description', 'account']