from django.contrib import admin
from .models import FundType, Fund, FundTransferHistory
# Register your models here.

admin.site.register(Fund)
admin.site.register(FundType)
admin.site.register(FundTransferHistory)
