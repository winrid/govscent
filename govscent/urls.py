"""govscent URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from govscentdotorg import views
from govscentdotorg.api import api_router

urlpatterns = [
    path('', views.index, name='index'),
    path('bill/<str:gov>/<str:gov_id>', views.bill_page, name='bill_page'),
    path('admin/', admin.site.urls),
    path('topic/<str:bill_topic_id>', views.topic_page, name='topic_page'),
    # This extra URL definition for the topic page is so we can optionally include some context in the URL.
    path('topic/<str:bill_topic_id>/<path:slug>', views.topic_page, name='topic_page_with_slug'),
    path('search/topic', views.topic_search_page, name="topic_search_page"),
    path('api/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls'))
]
