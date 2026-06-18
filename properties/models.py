from django.db import models
from django.conf import settings
import os


class Property(models.Model):
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    # Property details
    property_name = models.CharField(max_length=255)
    property_address = models.TextField()
    property_type = models.CharField(max_length=100)
    number_of_units = models.IntegerField()
    rentable_area = models.DecimalField(max_digits=12, decimal_places=2)
    year_built = models.IntegerField()
    year_renovated = models.IntegerField(null=True, blank=True)
    occupancy = models.DecimalField(max_digits=5, decimal_places=2)
    parking_spaces = models.IntegerField()

    # cover image for the property
    property_image = models.ImageField(upload_to='properties/images/', null=True, blank=True)

    # Ownership & meta
    sponsor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.property_name

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']


def property_document_upload_path(instance, filename):
    return f'properties/{instance.property.id}/documents/{filename}'


class PropertyDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=property_document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.property_name} - {self.file.name}"

    def delete(self, *args, **kwargs):
        # Remove physical file from storage
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Property Document'
        verbose_name_plural = 'Property Documents'
        ordering = ['-uploaded_at']



class PropertyDocumentChunk(models.Model):
    """
    Stores extracted text chunks and their embeddings for a PropertyDocument.
    Populated once during memorandum generation and reused on subsequent runs.
    """
    document   = models.ForeignKey(
        PropertyDocument,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    chunk_text  = models.TextField()
    embedding   = models.JSONField()          # stores list[float] (384-dim)
    chunk_index = models.PositiveIntegerField()  # order within the document

    class Meta:
        verbose_name        = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
        ordering            = ['document', 'chunk_index']

    def __str__(self):
        return f"{self.document} — chunk {self.chunk_index}"


class PropertyChatSession(models.Model):
    property   = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='chat_sessions')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_chat_sessions')
    title      = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Property Chat Session'
        verbose_name_plural = 'Property Chat Sessions'
        ordering            = ['-updated_at']

    def __str__(self):
        return f'{self.property.property_name} - {self.user.email} — {self.title or "Untitled"}'


class PropertyChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user',      'User'),
        ('assistant', 'Assistant'),
    ]

    session    = models.ForeignKey(PropertyChatSession, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Property Chat Message'
        verbose_name_plural = 'Property Chat Messages'
        ordering            = ['created_at']

    def __str__(self):
        return f'[{self.role}] {self.content[:60]}'