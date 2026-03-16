from rest_framework import serializers
from .models import Memorandum, MemorandumSection


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


class MemorandumSectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MemorandumSection
        fields = ['content']


class SectionImageSerializer(serializers.ModelSerializer):
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


class MemorandumListSerializer(serializers.ModelSerializer):
    property_name      = serializers.CharField(source='property.property_name', read_only=True)
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Memorandum
        fields = [
            'id', 'title', 'property', 'property_name', 'property_image_url',
            'status', 'mode', 'created_at',
        ]

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property.property_image and request:
            return request.build_absolute_uri(obj.property.property_image.url)
        return None


class MemorandumDetailSerializer(serializers.ModelSerializer):
    sections           = MemorandumSectionSerializer(many=True, read_only=True)
    property_name      = serializers.CharField(source='property.property_name', read_only=True)
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Memorandum
        fields = [
            'id', 'title', 'property', 'property_name', 'property_image_url',
            'status', 'mode', 'created_at', 'updated_at', 'sections',
        ]
        read_only_fields = ['id', 'property', 'created_at', 'updated_at', 'sections']

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property.property_image and request:
            return request.build_absolute_uri(obj.property.property_image.url)
        return None


class MemorandumUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Memorandum
        fields = ['title', 'status', 'mode']

    def validate_status(self, value):
        locked = {'Generating', 'Failed'}
        if value in locked:
            raise serializers.ValidationError(
                f"Cannot manually set status to '{value}'."
            )
        return value


class GenerateMemorandumSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()