from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Memorandum, MemorandumSection


class MemorandumSectionInline(TabularInline):
    model           = MemorandumSection
    extra           = 0
    readonly_fields = ['section_type', 'order', 'updated_at']
    fields          = ['section_type', 'order', 'content', 'image', 'updated_at']
    ordering        = ['order']


@admin.register(Memorandum)
class MemorandumAdmin(ModelAdmin):
    list_display    = ['title', 'property', 'sponsor', 'status', 'mode', 'created_at']
    list_filter     = ['status', 'mode']
    search_fields   = ['title', 'sponsor__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [MemorandumSectionInline]


@admin.register(MemorandumSection)
class MemorandumSectionAdmin(ModelAdmin):
    list_display    = ['memorandum', 'section_type', 'order', 'updated_at']
    list_filter     = ['section_type']
    search_fields   = ['memorandum__title']
    readonly_fields = ['updated_at']