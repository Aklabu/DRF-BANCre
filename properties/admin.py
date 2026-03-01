from django.contrib import admin
from .models import Property, PropertyDocument


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['property_name', 'property_type', 'sponsor', 'created_at']
    list_filter = ['property_type', 'created_at']
    search_fields = ['property_name', 'property_address', 'sponsor__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PropertyDocumentInline]

    fieldsets = (
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Property Details', {
            'fields': (
                'property_name', 'property_address', 'property_type',
                'number_of_units', 'rentable_area', 'year_built',
                'year_renovated', 'occupancy', 'parking_spaces',
            ),
        }),
        ('Ownership', {'fields': ('sponsor', 'created_at', 'updated_at')}),
    )


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['property__property_name', 'property__sponsor__email']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at']