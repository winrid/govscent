from django.contrib import admin
from django.urls import path, include

from govscentdotorg import views
from govscentdotorg.api import api_router

urlpatterns = [
    path('', views.index, name='index'),
    path('bill/<str:gov>/<str:gov_id>', views.bill_page, name='bill_page'),
    path('admin/', admin.site.urls),
    path('topic/<str:bill_topic_id>', views.topic_page, name='topic_page'),
    path('topic/<str:bill_topic_id>/<path:slug>', views.topic_page, name='topic_page_with_slug'),
    path('search/topic', views.topic_search_page, name="topic_search_page"),
    path('stats', views.stats_page, name="stats_page"),
    path('search/bill', views.bill_search_page, name="bill_search_page"),
    path('congress/<int:congress_number>', views.congress_page, name="congress_page"),
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls'))
]
