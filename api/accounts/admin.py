from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'mobile_no', 'is_verified', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'mobile_no', 'full_name')
    ordering = ('username',)
    readonly_fields = ('otp', 'otp_created_at', 'avatar_preview')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'mobile_no', 'avatar', 'avatar_preview')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'otp', 'otp_created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'password1', 'password2', 'role', 'mobile_no', 'is_verified', 'is_active', 'is_staff')}
        ),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return admin.utils.mark_safe(f'<img src="{obj.avatar.url}" style="max-height: 100px; max-width: 100px;" />')
        return "No Avatar"
    avatar_preview.short_description = 'Avatar Preview'