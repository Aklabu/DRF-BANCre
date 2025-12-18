from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTP


def send_otp_email(email, otp_code, otp_type):
    """Send OTP via email"""
    subject_map = {
        'signup': 'Verify Your Email - Signup OTP',
        'login_2fa': 'Two-Factor Authentication - Login OTP',
        'forgot_password': 'Password Reset - OTP Verification',
    }
    
    message_map = {
        'signup': f'Your OTP for email verification is: {otp_code}\n\nThis OTP will expire in 10 minutes.',
        'login_2fa': f'Your Two-Factor Authentication OTP is: {otp_code}\n\nThis OTP will expire in 10 minutes.',
        'forgot_password': f'Your password reset OTP is: {otp_code}\n\nThis OTP will expire in 10 minutes.',
    }
    
    subject = subject_map.get(otp_type, 'OTP Verification')
    message = message_map.get(otp_type, f'Your OTP is: {otp_code}')
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def create_otp(email, otp_type, remember_me=None):
    """Create and return OTP instance"""
    # Invalidate previous OTPs of same type for this email
    OTP.objects.filter(
        email=email,
        otp_type=otp_type,
        is_used=False
    ).update(is_used=True)
    
    otp_code = OTP.generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    otp = OTP.objects.create(
        email=email,
        otp_code=otp_code,
        otp_type=otp_type,
        expires_at=expires_at,
        remember_me=remember_me if otp_type == 'login_2fa' else None
    )
    
    # Send OTP via email
    send_otp_email(email, otp_code, otp_type)
    
    return otp


def verify_otp(email, otp_code, otp_type):
    """Verify OTP and return validation result"""
    try:
        otp = OTP.objects.get(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            is_used=False
        )
        
        if not otp.is_valid():
            return False, "OTP has expired."
        
        otp.is_used = True
        otp.save()
        
        return True, otp
    except OTP.DoesNotExist:
        return False, "Invalid OTP."