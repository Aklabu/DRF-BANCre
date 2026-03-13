from django.db import models
from django.conf import settings


class Notification(models.Model):

    # Notification type choices covering all platform events
    MEMORANDUM_GENERATED = 'MEMORANDUM_GENERATED'
    LOAN_REQUEST_CREATED = 'LOAN_REQUEST_CREATED'
    LOAN_REQUEST_UPDATED = 'LOAN_REQUEST_UPDATED'
    QUOTE_SUBMITTED      = 'QUOTE_SUBMITTED'
    QUOTE_ACCEPTED       = 'QUOTE_ACCEPTED'
    QUOTE_DECLINED       = 'QUOTE_DECLINED'
    MANUAL               = 'MANUAL'

    NOTIFICATION_TYPE_CHOICES = [
        (MEMORANDUM_GENERATED, 'Memorandum Generated'),
        (LOAN_REQUEST_CREATED, 'Loan Request Created'),
        (LOAN_REQUEST_UPDATED, 'Loan Request Updated'),
        (QUOTE_SUBMITTED,      'Quote Submitted'),
        (QUOTE_ACCEPTED,       'Quote Accepted'),
        (QUOTE_DECLINED,       'Quote Declined'),
        (MANUAL,               'Manual'),
    ]

    recipient         = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title             = models.CharField(max_length=255)
    message           = models.TextField()
    is_read           = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)

    # Plain integer references — intentionally not ForeignKeys to avoid cascade deletion
    # and to keep the notifications app decoupled from other apps
    memorandum_id   = models.IntegerField(null=True, blank=True)
    loan_request_id = models.IntegerField(null=True, blank=True)
    quote_id        = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'[{self.notification_type}] {self.recipient.email} — {self.title}'

    class Meta:
        verbose_name        = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering            = ['-created_at']


class NotificationPreference(models.Model):
    # Each user has one NotificationPreference record to manage their notification settings
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preference',
    )
    quote_emails_enabled = models.BooleanField(
        default=False,
        help_text='When enabled, the user receives emails for loan quote updates (new quote, accepted, declined).',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'NotificationPreference — {self.user.email} (quote emails: {self.quote_emails_enabled})'

    class Meta:
        verbose_name        = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'