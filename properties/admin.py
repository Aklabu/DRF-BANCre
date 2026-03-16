from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Property, PropertyDocument


class PropertyDocumentInline(TabularInline):
    model           = PropertyDocument
    extra           = 0
    readonly_fields = ['uploaded_at']


@admin.register(Property)
class PropertyAdmin(ModelAdmin):
    list_display    = ['property_name', 'property_type', 'sponsor', 'created_at']
    list_filter     = ['property_type']
    search_fields   = ['property_name', 'sponsor__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [PropertyDocumentInline]

    fieldsets = (
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Property Details', {
            'fields': (
                'property_name', 'property_address', 'property_type',
                'number_of_units', 'rentable_area', 'year_built',
                'year_renovated', 'occupancy', 'parking_spaces',
                'property_image',
            ),
        }),
        ('Ownership', {'fields': ('sponsor', 'created_at', 'updated_at')}),
    )


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(ModelAdmin):
    list_display    = ['id', 'property', 'file', 'uploaded_at']
    search_fields   = ['property__property_name']
    readonly_fields = ['uploaded_at']