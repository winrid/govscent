from django.contrib import admin

from govscentdotorg.models import Bill, BillAdmin
from govscentdotorg.models import BillTopic, BillTopicAdmin
from govscentdotorg.models import BillSection, BillSectionAdmin


admin.site.register(Bill, BillAdmin)
admin.site.register(BillTopic, BillTopicAdmin)
admin.site.register(BillSection, BillSectionAdmin)
