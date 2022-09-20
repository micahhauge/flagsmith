from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy


class CustomTokenAdmin(TokenAdmin):
    search_fields = ("key", "user__email")


# replace the token auth page to add a search
admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, CustomTokenAdmin)
