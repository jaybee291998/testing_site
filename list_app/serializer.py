from rest_framework import serializers
from .models import List

class ListSerializer(serializers.ModelSerializer):
	class Meta:
		model = List 
		fields = ['id', 'user', 'name', 'content', 'last_modified', 'timestamp']