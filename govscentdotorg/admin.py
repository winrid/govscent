from django.contrib import admin

from govscentdotorg.models import Bill, BillTopic, BillAdmin

admin.site.register(Bill, BillAdmin)
admin.site.register(BillTopic)
