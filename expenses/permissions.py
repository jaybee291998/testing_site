from datetime import datetime, timedelta

from django.utils import timezone

from rest_framework import permissions


class OwnerAndSuperUserOnly(permissions.BasePermission):

	def has_permission(self, request, view):
		if request.user.is_authenticated:
			return True

	def has_object_permission(self, request, view, obj):
		if request.user.is_superuser:
			return True

		if obj.account == request.user.bank_account:
			return True
			
class ExpiredObjectSuperUserOnly(permissions.BasePermission):

	def has_permission(self, request, view):
		if request.user.is_authenticated:
			return True

	def has_object_permission(self, request, view, obj):
		if obj.account == request.user.bank_account:
			if not self.object_expired(obj):
				return True
		if request.user.is_superuser:
			return True
		print(f'expired: {self.object_expired(obj)}')

		return False


	def object_expired(self, odj):
		expired_on = timezone.make_aware(datetime.now() - timedelta(minutes=10))
		return obj.timestamp < expired_on