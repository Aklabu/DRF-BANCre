from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import LoanRequest, LoanQuote


class LoanQuoteInline(TabularInline):
    model            = LoanQuote
    extra            = 0
    readonly_fields  = ['lender', 'lender_name', 'status', 'submitted_at', 'loan_amount', 'interest_rate']
    fields           = ['lender', 'lender_name', 'loan_amount', 'interest_rate', 'status', 'submitted_at']
    show_change_link = True


@admin.register(LoanRequest)
class LoanRequestAdmin(ModelAdmin):
    list_display    = ['id', 'property', 'sponsor', 'requested_amount', 'loan_term', 'ltv', 'status', 'created_at']
    list_filter     = ['status']
    search_fields   = ['property__property_name', 'sponsor__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [LoanQuoteInline]


@admin.register(LoanQuote)
class LoanQuoteAdmin(ModelAdmin):
    list_display    = ['id', 'lender_name', 'loan_request', 'loan_amount', 'interest_rate', 'status', 'submitted_at']
    list_filter     = ['status']
    search_fields   = ['lender_name', 'lender__email']
    readonly_fields = ['submitted_at', 'updated_at']