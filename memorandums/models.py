from django.db import models
from django.conf import settings


class Memorandum(models.Model):
    STATUS_CHOICES = [
        ('Generating', 'Generating'),
        ('Draft',      'Draft'),
        ('Failed',     'Failed'),
        ('Published',  'Published'),
    ]
    MODE_CHOICES = [
        ('Editor',  'Editor'),
        ('Preview', 'Preview'),
    ]

    property  = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='memorandums',
    )
    sponsor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memorandums',
    )
    title      = models.CharField(max_length=255)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Generating')
    mode       = models.CharField(max_length=10, choices=MODE_CHOICES,   default='Editor')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name        = 'Memorandum'
        verbose_name_plural = 'Memorandums'
        ordering            = ['-created_at']


def section_image_upload_path(instance, filename):
    return f'memorandums/{instance.memorandum.id}/sections/{filename}'


class MemorandumSection(models.Model):
    SECTION_TYPE_CHOICES = [
        ('property_information', 'Property Information'),
        ('executive_summary',    'Executive Summary'),
        ('property_overview',    'Property Overview'),
        ('property_highlights',  'Property Highlights'),
        ('area_overview',        'Area Overview'),
        ('area_highlights',      'Area Highlights'),
        ('market_summary',       'Market Summary'),
        ('financing_summary',    'Financing Summary'),
        ('financial_analysis',   'Financial Analysis'),
        ('sales_comparables',    'Sales Comparables'),
        ('lease_comparables',    'Lease Comparables'),
        ('area_amenities',       'Area Amenities'),
        ('sponsorship',          'Sponsorship'),
        ('disclaimer',           'Disclaimer'),
    ]

    memorandum   = models.ForeignKey(
        Memorandum,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    section_type = models.CharField(max_length=50, choices=SECTION_TYPE_CHOICES)
    content      = models.TextField(blank=True, default='')
    image        = models.ImageField(
        upload_to=section_image_upload_path,
        null=True,
        blank=True,
    )
    order      = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.memorandum.title} — {self.get_section_type_display()}'

    class Meta:
        verbose_name        = 'Memorandum Section'
        verbose_name_plural = 'Memorandum Sections'
        ordering            = ['order']
        unique_together     = [('memorandum', 'section_type')]