from django.urls import path
from .views import (
    SignupView, ResendSignupOTPView, VerifySignupOTPView,
    LoginView, VerifyLogin2FAView, ResendLogin2FAOTPView,
    Toggle2FAView, ForgotPasswordView, ResendForgotPasswordOTPView,
    VerifyForgotPasswordOTPView, ResetPasswordView,
    ChangePasswordView, LogoutView, ProfileView, TokenRefreshView
)

app_name = 'accounts'

urlpatterns = [
    # Signup & Verification
    path('signup/', SignupView.as_view(), name='signup'),
    path('resend-otp/', ResendSignupOTPView.as_view(), name='resend-signup-otp'),
    path('verify-otp/', VerifySignupOTPView.as_view(), name='verify-signup-otp'),
    
    # Login & 2FA
    path('login/', LoginView.as_view(), name='login'),
    path('login/verify-2fa/', VerifyLogin2FAView.as_view(), name='verify-login-2fa'),
    path('login/resend-2fa-otp/', ResendLogin2FAOTPView.as_view(), name='resend-login-2fa-otp'),
    
    # 2FA Toggle
    path('two-factor/toggle/', Toggle2FAView.as_view(), name='toggle-2fa'),
    
    # Forgot Password
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('forgot-password/resend/', ResendForgotPasswordOTPView.as_view(), name='resend-forgot-password-otp'),
    path('forgot-password/verify-otp/', VerifyForgotPasswordOTPView.as_view(), name='verify-forgot-password-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    
    # Change Password & Logout
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
]