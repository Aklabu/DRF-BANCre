from django.core.mail import send_mail
from django.conf import settings


def _send(subject: str, message: str, recipient_email: str) -> None:
    # fire-and-forget email sending, with silent failure to avoid disrupting user experience
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=True,
        )
    except Exception:
        pass


def notify_sponsor_new_quote(loan_request, quote) -> None:
    # Notify the sponsor that a new quote has been submitted on their loan request.
    subject = f'New Quote Received — {loan_request.property.property_name}'
    message = (
        f'Hello {loan_request.sponsor.first_name},\n\n'
        f'A new quote has been submitted by {quote.lender_name} for your loan request '
        f'on {loan_request.property.property_name}.\n\n'
        f'Loan Amount: ${quote.loan_amount}\n'
        f'Interest Rate: {quote.interest_rate}%\n'
        f'Term: {quote.term} months\n\n'
        f'Log in to review and compare quotes.\n\nBancre Team'
    )
    _send(subject, message, loan_request.sponsor.email)


def notify_lender_quote_accepted(quote) -> None:
    # Notify the lender that their quote has been accepted.
    subject = f'Your Quote Has Been Accepted — {quote.loan_request.property.property_name}'
    message = (
        f'Hello {quote.lender_name},\n\n'
        f'Congratulations! Your quote for the loan request on '
        f'{quote.loan_request.property.property_name} has been accepted.\n\n'
        f'Log in to view the full details.\n\nBancre Team'
    )
    _send(subject, message, quote.lender.email)


def notify_lender_quote_declined(quote) -> None:
   # Notify the lender that their quote has been declined.
    subject = f'Your Quote Has Been Declined — {quote.loan_request.property.property_name}'
    message = (
        f'Hello {quote.lender_name},\n\n'
        f'Your quote for the loan request on '
        f'{quote.loan_request.property.property_name} has been declined.\n\n'
        f'Thank you for your participation.\n\nBancre Team'
    )
    _send(subject, message, quote.lender.email)