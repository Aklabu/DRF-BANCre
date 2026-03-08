from django.contrib import admin
from .models import LoanRequest, LoanQuote


class LoanQuoteInline(admin.TabularInline):
    model           = LoanQuote
    extra           = 0
    readonly_fields = ['lender', 'lender_name', 'status', 'submitted_at', 'loan_amount', 'interest_rate']
    fields          = ['lender', 'lender_name', 'loan_amount', 'interest_rate', 'status', 'submitted_at']
    show_change_link = True


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display    = ['id', 'property', 'sponsor', 'requested_amount', 'loan_term', 'ltv', 'status', 'created_at']
    list_filter     = ['status', 'created_at']
    search_fields   = ['property__property_name', 'sponsor__email']
    ordering        = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [LoanQuoteInline]

    fieldsets = (
        ('Loan Details',  {'fields': ('property', 'sponsor', 'requested_amount', 'loan_term', 'ltv', 'status')}),
        ('Timestamps',    {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(LoanQuote)
class LoanQuoteAdmin(admin.ModelAdmin):
    list_display    = ['id', 'lender_name', 'loan_request', 'loan_amount', 'interest_rate', 'status', 'submitted_at']
    list_filter     = ['status', 'submitted_at']
    search_fields   = ['lender_name', 'lender__email', 'loan_request__property__property_name']
    ordering        = ['-submitted_at']
    readonly_fields = ['submitted_at', 'updated_at']

    fieldsets = (
        ('Basic Information',     {'fields': ('loan_request', 'lender', 'lender_name', 'guarantor', 'status', 'expires_at', 'submitted_at', 'updated_at')}),
        ('Loan Structure',        {'fields': ('loan_amount', 'initial_funding', 'future_funding', 'sponsor_equity')}),
        ('LTV & Debt Yield',      {'fields': ('max_as_is_ltv', 'max_ltc', 'max_as_stabilized_ltv', 'min_as_is_dy', 'min_stabilized_dy')}),
        ('Terms & Rates',         {'fields': ('term', 'interest_rate', 'amortization', 'prepayment')}),
        ('Fees',                  {'fields': ('origination_fee', 'capex_reserve', 'ff_and_e_reserve', 'interest_carry_reserve')}),
        ('Additional Terms',      {'fields': ('extension_conditions', 'collateral', 'recourse')}),
    )