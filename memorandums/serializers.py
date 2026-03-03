from rest_framework import serializers
from .models import Memorandum, MemorandumSection


# Serializers for Memorandum and its sections, used in API endpoints
class MemorandumSectionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = MemorandumSection
        fields = [
            'id', 'section_type', 'content',
            'image', 'image_url', 'order', 'updated_at',
        ]
        read_only_fields = ['id', 'section_type', 'order', 'updated_at', 'image_url']
        extra_kwargs = {'image': {'write_only': True}}

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# Create and update serializers for Memorandum and its sections, with validation logic
class MemorandumSectionUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH /sections/{section_id}/ — only content is updatable here."""

    class Meta:
        model  = MemorandumSection
        fields = ['content']


# Upload image for a section, with validation to ensure only allowed types are uploaded
class SectionImageSerializer(serializers.ModelSerializer):
    """Used for POST /sections/{section_id}/image/"""

    class Meta:
        model  = MemorandumSection
        fields = ['image']

    def validate_image(self, value):
        allowed = {'jpg', 'jpeg', 'png'}
        ext = value.name.rsplit('.', 1)[-1].lower()
        if ext not in allowed:
            raise serializers.ValidationError(
                f"Unsupported image type '.{ext}'. Allowed: jpg, jpeg, png."
            )
        return value


# Main serializers for Memorandum list and detail views, with nested sections and property name
class MemorandumListSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.property_name', read_only=True)

    class Meta:
        model  = Memorandum
        fields = [
            'id', 'title', 'property', 'property_name',
            'status', 'mode', 'created_at',
        ]


# Detail serializer includes all sections and property name, but sections are read-only here
class MemorandumDetailSerializer(serializers.ModelSerializer):
    sections      = MemorandumSectionSerializer(many=True, read_only=True)
    property_name = serializers.CharField(source='property.property_name', read_only=True)

    class Meta:
        model  = Memorandum
        fields = [
            'id', 'title', 'property', 'property_name',
            'status', 'mode', 'created_at', 'updated_at', 'sections',
        ]
        read_only_fields = ['id', 'property', 'created_at', 'updated_at', 'sections']


# Allow updating only title, status, and mode of the memorandum
class MemorandumUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH /memorandums/{id}/ — title, status, mode only."""

    class Meta:
        model  = Memorandum
        fields = ['title', 'status', 'mode']

    def validate_status(self, value):
        # Don't allow manually setting status back to Generating or Failed
        locked = {'Generating', 'Failed'}
        if value in locked:
            raise serializers.ValidationError(
                f"Cannot manually set status to '{value}'."
            )
        return value


# generating new memorandum based on property data
class GenerateMemorandumSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()