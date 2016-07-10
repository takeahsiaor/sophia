from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from sophia import urls as sophia_urls

urlpatterns = [
    url(r'^', include(sophia_urls))
]