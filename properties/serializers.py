from rest_framework import serializers
from .models import Property, PropertyDocument


class PropertyDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyDocument
        fields = ['id', 'file_url', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class PropertySerializer(serializers.ModelSerializer):
    documents = PropertyDocumentSerializer(many=True, read_only=True)
    sponsor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'latitude', 'longitude', 'property_name', 'property_address',
            'property_type', 'number_of_units', 'rentable_area', 'year_built',
            'year_renovated', 'occupancy', 'parking_spaces',
            'sponsor', 'created_at', 'updated_at', 'documents',
        ]
        read_only_fields = ['id', 'sponsor', 'created_at', 'updated_at', 'documents']

    def validate_occupancy(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Occupancy must be between 0.00 and 100.00.')
        return value


class PropertyListSerializer(serializers.ModelSerializer):
    # Lightweight serializer for list view (no documents)
    class Meta:
        model = Property
        fields = [
            'id', 'property_name', 'property_address', 'property_type',
            'latitude', 'longitude', 'created_at', 'updated_at',
        ]


class PropertyMapSerializer(serializers.ModelSerializer):
    # Minimal fields for lender map
    class Meta:
        model = Property
        fields = ['id', 'property_name', 'property_address', 'property_type', 'latitude', 'longitude']