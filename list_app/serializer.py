from rest_framework import serializers
from .models import List

class ListSerializer(serializers.ModelSerializer):
	user 		= serializers.ReadOnlyField(source='')
	class Meta:
		model = List 
		fields = ['id', 'user', 'name', 'content', 'last_modified', 'timestamp']
		extra_kwargs = {
			'user':{
				'default':serializers.CreateOnlyDefault(
					serializers.CurrentUserDefault()
				),
				'read_only':True
			}
		}