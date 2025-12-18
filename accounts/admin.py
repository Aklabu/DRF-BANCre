from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MediaFile, OTP, PasswordResetSession


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'customer_type', 'is_verified', 'two_factor_enabled', 'is_active']
    list_filter = ['customer_type', 'is_verified', 'two_factor_enabled', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'company_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'customer_type', 'profile_photo')}),
        ('Company Information', {'fields': ('company_name', 'position', 'street_address', 'city', 'state', 'zip_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'two_factor_enabled', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'customer_type', 'password1', 'password2', 'is_verified'),
        }),
    )


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['user__email']
    ordering = ['-uploaded_at']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp_code', 'otp_type', 'is_used', 'created_at', 'expires_at']
    list_filter = ['otp_type', 'is_used', 'created_at']
    search_fields = ['email', 'otp_code']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(PasswordResetSession)
class PasswordResetSessionAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp_verified', 'created_at', 'expires_at']
    list_filter = ['otp_verified', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']