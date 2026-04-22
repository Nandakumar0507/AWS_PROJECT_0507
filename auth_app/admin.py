from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClinicianProfile, CustomUser, PatientProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "username", "role", "is_staff")
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("role", "display_name")}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "role", "display_name")}),)
    ordering = ("email",)


admin.site.register(PatientProfile)
admin.site.register(ClinicianProfile)
