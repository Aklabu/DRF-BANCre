from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, PasswordResetSession
from .serializers import (
    SignupSerializer, LoginSerializer, VerifyOTPSerializer,
    ResendOTPSerializer, Toggle2FASerializer, ForgotPasswordSerializer,
    ResetPasswordSerializer, ChangePasswordSerializer, LogoutSerializer,
    UserProfileSerializer, UpdateProfileSerializer, TokenRefreshSerializer
)
from .utils import create_otp, verify_otp
from utils.response import CustomResponse


class SignupView(APIView):
    # User Registration View
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        user = serializer.save()
        
        # Create and send OTP
        create_otp(user.email, 'signup')
        
        return CustomResponse.success(
            message="OTP sent to your email",
            data={"email": user.email},
            status_code=status.HTTP_201_CREATED
        )


class ResendSignupOTPView(APIView):
    # Login, 2FA, and Password Management Views
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email, is_verified=False)
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User not found or already verified",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        create_otp(email, 'signup')
        
        return CustomResponse.success(
            message="A new OTP has been sent",
            status_code=status.HTTP_200_OK
        )


class VerifySignupOTPView(APIView):
    # View to verify signup OTP and complete registration
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        is_valid, result = verify_otp(email, otp_code, 'signup')
        
        if not is_valid:
            return CustomResponse.error(
                message=result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark user as verified
        try:
            user = CustomUser.objects.get(email=email)
            user.is_verified = True
            user.save()
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return CustomResponse.success(
            message="Verification successful. Registration completed.",
            status_code=status.HTTP_200_OK
        )


class LoginView(APIView):
    # User Login View with optional 2FA
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        remember_me = serializer.validated_data['remember_me']
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return CustomResponse.error(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_verified:
            return CustomResponse.error(
                message="Please verify your email before logging in",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if 2FA is enabled
        if user.two_factor_enabled:
            # Send 2FA OTP
            create_otp(email, 'login_2fa', remember_me=remember_me)
            
            return CustomResponse.success(
                message="OTP sent to your email for two-factor authentication",
                data={
                    "requires_2fa": True,
                    "email": email
                },
                status_code=status.HTTP_200_OK
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Set token expiration based on remember_me
        if not remember_me:
            refresh.set_exp(lifetime=timedelta(hours=1))
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "customer_type": user.customer_type,
        }
        
        return CustomResponse.success(
            message="Login successful",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data
            },
            status_code=status.HTTP_200_OK
        )


class VerifyLogin2FAView(APIView):
    # View to verify 2FA OTP during login
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        is_valid, result = verify_otp(email, otp_code, 'login_2fa')
        
        if not is_valid:
            return CustomResponse.error(
                message=result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user and remember_me preference
        try:
            user = CustomUser.objects.get(email=email)
            remember_me = result.remember_me if result.remember_me is not None else False
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        if not remember_me:
            refresh.set_exp(lifetime=timedelta(hours=1))
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "customer_type": user.customer_type,
        }
        
        return CustomResponse.success(
            message="Two-factor authentication successful",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data
            },
            status_code=status.HTTP_200_OK
        )


class ResendLogin2FAOTPView(APIView):
    # View to resend 2FA OTP during login
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email, is_verified=True)
            if not user.two_factor_enabled:
                return CustomResponse.error(
                    message="Two-factor authentication is not enabled for this account",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        create_otp(email, 'login_2fa')
        
        return CustomResponse.success(
            message="A new 2FA OTP has been sent",
            status_code=status.HTTP_200_OK
        )


class Toggle2FAView(APIView):
    # View to enable or disable two-factor authentication for the user
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        serializer = Toggle2FASerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        enable_2fa = serializer.validated_data['enable_2fa']
        user = request.user
        
        user.two_factor_enabled = enable_2fa
        user.save()
        
        message = f"Two-factor authentication {'enabled' if enable_2fa else 'disabled'} successfully"
        
        return CustomResponse.success(
            message=message,
            data={"two_factor_enabled": user.two_factor_enabled},
            status_code=status.HTTP_200_OK
        )


class ForgotPasswordView(APIView):
    # View to initiate forgot password process by sending OTP to user's email
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User with this email does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        create_otp(email, 'forgot_password')
        
        return CustomResponse.success(
            message="OTP sent to your email",
            status_code=status.HTTP_200_OK
        )


class ResendForgotPasswordOTPView(APIView):
    # View to resend OTP for forgot password process
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        
        try:
            CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User with this email does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        create_otp(email, 'forgot_password')
        
        return CustomResponse.success(
            message="A new OTP has been sent",
            status_code=status.HTTP_200_OK
        )


class VerifyForgotPasswordOTPView(APIView):
    # View to verify OTP for forgot password process
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        is_valid, result = verify_otp(email, otp_code, 'forgot_password')
        
        if not is_valid:
            return CustomResponse.error(
                message=result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create password reset session
        PasswordResetSession.objects.filter(email=email).delete()
        
        PasswordResetSession.objects.create(
            email=email,
            otp_verified=True,
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        return CustomResponse.success(
            message="OTP verified. You may now reset your password.",
            status_code=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    # View to reset password after verifying forgot password OTP
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        
        # Verify reset session
        try:
            reset_session = PasswordResetSession.objects.get(email=email)
            if not reset_session.is_valid():
                return CustomResponse.error(
                    message="Password reset session has expired. Please request a new OTP.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except PasswordResetSession.DoesNotExist:
            return CustomResponse.error(
                message="Please verify OTP first",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Delete reset session
            reset_session.delete()
        except CustomUser.DoesNotExist:
            return CustomResponse.error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return CustomResponse.success(
            message="Password reset successfully.",
            status_code=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    # View to allow authenticated users to change their password
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        
        if not user.check_password(current_password):
            return CustomResponse.error(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return CustomResponse.success(
            message="Password updated successfully.",
            status_code=status.HTTP_200_OK
        )


class TokenRefreshView(APIView):
    # View to obtain a new access token using a valid refresh token
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )

        try:
            refresh = RefreshToken(serializer.validated_data['refresh_token'])
            return CustomResponse.success(
                message="Token refreshed successfully",
                data={"access": str(refresh.access_token)},
                status_code=status.HTTP_200_OK
            )
        except Exception:
            return CustomResponse.error(
                message="Invalid or expired refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    # View to handle user logout by blacklisting the refresh token
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            refresh_token = serializer.validated_data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return CustomResponse.error(
                message="Invalid token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return CustomResponse.success(
            message="Successfully logged out.",
            status_code=status.HTTP_200_OK
        )


class ProfileView(APIView):
    # View to retrieve and update user profile information
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        
        return CustomResponse.success(
            message="Profile retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    def patch(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return CustomResponse.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        serializer.save()
        
        # Return updated profile
        profile_serializer = UserProfileSerializer(user)
        
        return CustomResponse.success(
            message="Profile updated successfully",
            data={"profile": profile_serializer.data},
            status_code=status.HTTP_200_OK
        )