from rest_framework import serializers
from .models import CustomUser, MediaFile
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'customer_type', 'first_name', 'last_name', 
            'email', 'phone', 'password', 'confirm_password', 'media_files'
        ]
    
    def validate(self, data):
        # Password match validation
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        
        # Password strength validation
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        # Media files validation for Broker and Lender
        customer_type = data.get('customer_type')
        media_files = data.get('media_files', [])
        
        if customer_type in ['Broker', 'Lender']:
            if not media_files:
                raise serializers.ValidationError({
                    "media_files": "Media files are required for Broker and Lender."
                })
            if len(media_files) < 1:
                raise serializers.ValidationError({
                    "media_files": "At least 1 media file is required."
                })
            if len(media_files) > 5:
                raise serializers.ValidationError({
                    "media_files": "Maximum 5 media files are allowed."
                })
        elif customer_type == 'Sponsor' and media_files:
            raise serializers.ValidationError({
                "media_files": "Media files are not allowed for Sponsor."
            })
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        media_files = validated_data.pop('media_files', [])
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create media files
        for file in media_files:
            MediaFile.objects.create(user=user, file=file)
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=False)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class Toggle2FASerializer(serializers.Serializer):
    enable_2fa = serializers.BooleanField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({
                "confirm_new_password": "Passwords do not match."
            })
        
        try:
            validate_password(data['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        
        try:
            validate_password(data['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    company_information = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'profile_photo', 'company_information'
        ]
        read_only_fields = ['email']
    
    def get_company_information(self, obj):
        return {
            'company_name': obj.company_name,
            'position': obj.position,
            'street_address': obj.street_address,
            'city': obj.city,
            'state': obj.state,
            'zip_code': obj.zip_code,
        }


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone', 'profile_photo',
            'company_name', 'position', 'street_address',
            'city', 'state', 'zip_code'
        ]
    
    def validate_email(self, value):
        raise serializers.ValidationError("Email cannot be updated.")
    
    def validate_customer_type(self, value):
        raise serializers.ValidationError("Customer type cannot be updated.")