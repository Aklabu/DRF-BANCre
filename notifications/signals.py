from django.db.models.signals import post_save
from django.dispatch import receiver


# Memorandum signals
@receiver(post_save, sender='memorandums.Memorandum')
def on_memorandum_saved(sender, instance, created, **kwargs):
    # Only notify when generation is complete — status just became Draft
    if instance.status != 'Draft':
        return

    # Avoid duplicate notifications — only fire when transitioning to Draft
    # We detect this by checking if the previous status was Generating
    # The _pre_status attribute is set by the pre_save signal below
    previous_status = getattr(instance, '_pre_status', None)
    if previous_status != 'Generating':
        return

    from .models import Notification

    property_name = instance.property.property_name

    Notification.objects.create(
        recipient         = instance.sponsor,
        notification_type = Notification.MEMORANDUM_GENERATED,
        title             = 'Memorandum Ready',
        message           = f'Your offering memorandum for {property_name} has been successfully generated.',
        memorandum_id     = instance.id,
    )


# Loan Request signals
@receiver(post_save, sender='loans.LoanRequest')
def on_loan_request_saved(sender, instance, created, **kwargs):
    from .models import Notification
    from django.contrib.auth import get_user_model

    User         = get_user_model()
    property_name = instance.property.property_name

    if created:
        # Broadcast to all lenders when a new loan request is created
        lenders = User.objects.filter(customer_type='Lender', is_active=True)

        # Use bulk_create for efficiency — never loop and create one by one
        notifications = [
            Notification(
                recipient         = lender,
                notification_type = Notification.LOAN_REQUEST_CREATED,
                title             = 'New Loan Request Available',
                message           = (
                    f'A new loan request has been listed for {property_name}. '
                    f'Requested amount: ${instance.requested_amount}.'
                ),
                loan_request_id   = instance.id,
            )
            for lender in lenders
        ]
        Notification.objects.bulk_create(notifications)

    else:
        # Broadcast to all lenders when an existing loan request is updated
        lenders = User.objects.filter(customer_type='Lender', is_active=True)

        notifications = [
            Notification(
                recipient         = lender,
                notification_type = Notification.LOAN_REQUEST_UPDATED,
                title             = 'Loan Request Updated',
                message           = f'A loan request for {property_name} has been updated by the sponsor.',
                loan_request_id   = instance.id,
            )
            for lender in lenders
        ]
        Notification.objects.bulk_create(notifications)


# Loan Quote signals
@receiver(post_save, sender='loans.LoanQuote')
def on_loan_quote_saved(sender, instance, created, **kwargs):
    from .models import Notification

    property_name = instance.loan_request.property.property_name

    if created:
        # Notify the sponsor when a lender submits a new quote
        Notification.objects.create(
            recipient         = instance.loan_request.sponsor,
            notification_type = Notification.QUOTE_SUBMITTED,
            title             = 'New Quote Received',
            message           = f'A lender has submitted a quote for your loan request on {property_name}.',
            loan_request_id   = instance.loan_request.id,
            quote_id          = instance.id,
        )
        return

    # Status change detection — compare current status to previous status
    # _pre_status is set by the pre_save signal below before the model is saved
    previous_status = getattr(instance, '_pre_status', None)
    current_status  = instance.status

    # Do nothing if status has not changed
    if previous_status == current_status:
        return

    if current_status == 'Accepted':
        # Notify the lender that their quote was accepted
        Notification.objects.create(
            recipient         = instance.lender,
            notification_type = Notification.QUOTE_ACCEPTED,
            title             = 'Your Quote Was Accepted',
            message           = f'Congratulations! Your quote for {property_name} has been accepted by the sponsor.',
            loan_request_id   = instance.loan_request.id,
            quote_id          = instance.id,
        )

    elif current_status == 'Declined':
        # Notify the lender that their quote was declined
        Notification.objects.create(
            recipient         = instance.lender,
            notification_type = Notification.QUOTE_DECLINED,
            title             = 'Your Quote Was Declined',
            message           = f'Your quote for {property_name} has been declined by the sponsor.',
            loan_request_id   = instance.loan_request.id,
            quote_id          = instance.id,
        )


# Pre-save signals to capture previous status before it is overwritten
from django.db.models.signals import pre_save

@receiver(pre_save, sender='memorandums.Memorandum')
def capture_memorandum_pre_status(sender, instance, **kwargs):
    # Store the current DB status on the instance before it gets overwritten
    if not instance.pk:
        return
    try:
        instance._pre_status = sender.objects.get(pk=instance.pk).status
    except sender.DoesNotExist:
        instance._pre_status = None


@receiver(pre_save, sender='loans.LoanQuote')
def capture_quote_pre_status(sender, instance, **kwargs):
    # Store the current DB status on the instance before it gets overwritten
    if not instance.pk:
        return
    try:
        instance._pre_status = sender.objects.get(pk=instance.pk).status
    except sender.DoesNotExist:
        instance._pre_status = None