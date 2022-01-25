from rest_framework import permissions

class IsOwner(permissions.BasePermission):
	"""
		Only allow the owner of an object to retrieve, update or destroy the object
	"""

	def has_object_permission(self, request, view, obj):
		return obj.user == request.user