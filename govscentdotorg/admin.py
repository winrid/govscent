from django.contrib import admin

from govscentdotorg.models import Bill, BillAdmin
from govscentdotorg.models import BillTopic, BillTopicAdmin

admin.site.register(Bill, BillAdmin)
admin.site.register(BillTopic, BillTopicAdmin)
