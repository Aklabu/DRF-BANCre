from rest_framework import serializers
from .models import Property, PropertyDocument


class PropertyDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model  = PropertyDocument
        fields = ['id', 'file_url', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class PropertySerializer(serializers.ModelSerializer):
    documents          = PropertyDocumentSerializer(many=True, read_only=True)
    sponsor            = serializers.StringRelatedField(read_only=True)
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = [
            'id', 'latitude', 'longitude', 'property_name', 'property_address',
            'property_type', 'number_of_units', 'rentable_area', 'year_built',
            'year_renovated', 'occupancy', 'parking_spaces',
            'property_image', 'property_image_url',
            'sponsor', 'created_at', 'updated_at', 'documents',
        ]
        read_only_fields = ['id', 'sponsor', 'created_at', 'updated_at', 'documents', 'property_image_url']
        # property_image is write-only — use property_image_url for reading
        extra_kwargs = {'property_image': {'write_only': True}}

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property_image and request:
            return request.build_absolute_uri(obj.property_image.url)
        return None

    def validate_occupancy(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Occupancy must be between 0.00 and 100.00.')
        return value


class PropertyListSerializer(serializers.ModelSerializer):
    # lightweight serializer for list view — no documents
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = [
            'id', 'property_name', 'property_address', 'property_type',
            'latitude', 'longitude', 'property_image_url', 'created_at', 'updated_at',
        ]

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property_image and request:
            return request.build_absolute_uri(obj.property_image.url)
        return None


class PropertyMapSerializer(serializers.ModelSerializer):
    # minimal fields for lender map
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = ['id', 'property_name', 'property_address', 'property_type', 'latitude', 'longitude', 'property_image_url']

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property_image and request:
            return request.build_absolute_uri(obj.property_image.url)
        return None