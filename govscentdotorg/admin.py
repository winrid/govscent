from django.contrib import admin

from govscentdotorg.models import Bill, BillTags, BillTopic, BillAdmin

admin.site.register(Bill, BillAdmin)
admin.site.register(BillTags)
admin.site.register(BillTopic)
