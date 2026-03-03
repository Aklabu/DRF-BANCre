from celery import shared_task
from django.apps import apps


# Section display order — matches SECTIONS list in extractors.py
SECTION_ORDER = [
    'property_information',
    'executive_summary',
    'property_overview',
    'property_highlights',
    'area_overview',
    'area_highlights',
    'market_summary',
    'financing_summary',
    'financial_analysis',
    'sales_comparables',
    'lease_comparables',
    'area_amenities',
    'sponsorship',
    'disclaimer',
]


@shared_task(bind=True, max_retries=1)
def generate_memorandum_task(self, memorandum_id: int):
    """
    Background Celery task that:
      1. Fetches the Memorandum and its related Property + documents.
      2. Calls generate_memorandum() from ai_files/.
      3. Creates 14 MemorandumSection records.
      4. Sets status to 'Draft' on success or 'Failed' on error.
    """
    Memorandum        = apps.get_model('memorandums', 'Memorandum')
    MemorandumSection = apps.get_model('memorandums', 'MemorandumSection')

    try:
        memorandum = Memorandum.objects.select_related('property').get(pk=memorandum_id)
    except Memorandum.DoesNotExist:
        return

    try:
        prop = memorandum.property

        # Build property data dict
        property_data = {
            'property_name':    prop.property_name,
            'property_address': prop.property_address,
            'property_type':    prop.property_type,
            'number_of_units':  prop.number_of_units,
            'rentable_area':    str(prop.rentable_area),
            'year_built':       prop.year_built,
            'year_renovated':   prop.year_renovated,
            'occupancy':        str(prop.occupancy),
            'parking_spaces':   prop.parking_spaces,
            'latitude':         str(prop.latitude),
            'longitude':        str(prop.longitude),
        }

        # Collect absolute file paths for all property documents
        document_paths = [
            doc.file.path
            for doc in prop.documents.all()
            if doc.file
        ]

        # Call the single AI entry point
        from .ai_files import generate_memorandum
        sections_data = generate_memorandum(memorandum_id, property_data, document_paths)

        # Create MemorandumSection records
        sections_to_create = []
        for order, section_key in enumerate(SECTION_ORDER):
            content = sections_data.get(section_key, '')
            sections_to_create.append(
                MemorandumSection(
                    memorandum=memorandum,
                    section_type=section_key,
                    content=content,
                    order=order,
                )
            )
        MemorandumSection.objects.bulk_create(sections_to_create)

        # Mark as Draft
        memorandum.status = 'Draft'
        memorandum.save(update_fields=['status', 'updated_at'])

    except Exception as exc:
        # Mark as Failed so the frontend can surface the error
        Memorandum.objects.filter(pk=memorandum_id).update(status='Failed')
        raise self.retry(exc=exc, countdown=0)