from django.contrib import admin
from .models import Memorandum, MemorandumSection


class MemorandumSectionInline(admin.TabularInline):
    model          = MemorandumSection
    extra          = 0
    readonly_fields = ['section_type', 'order', 'updated_at']
    fields         = ['section_type', 'order', 'content', 'image', 'updated_at']
    ordering       = ['order']


@admin.register(Memorandum)
class MemorandumAdmin(admin.ModelAdmin):
    list_display   = ['title', 'property', 'sponsor', 'status', 'mode', 'created_at']
    list_filter    = ['status', 'mode', 'created_at']
    search_fields  = ['title', 'sponsor__email', 'property__property_name']
    ordering       = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines        = [MemorandumSectionInline]

    fieldsets = (
        (None, {'fields': ('title', 'property', 'sponsor', 'status', 'mode')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(MemorandumSection)
class MemorandumSectionAdmin(admin.ModelAdmin):
    list_display   = ['memorandum', 'section_type', 'order', 'updated_at']
    list_filter    = ['section_type', 'updated_at']
    search_fields  = ['memorandum__title', 'memorandum__sponsor__email']
    ordering       = ['memorandum', 'order']
    readonly_fields = ['updated_at']