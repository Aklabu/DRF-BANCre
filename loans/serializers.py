from rest_framework import serializers
from .models import LoanRequest, LoanQuote


class LoanRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LoanRequest
        fields = ['property', 'requested_amount', 'loan_term', 'ltv']

    def validate_property(self, value):
        request = self.context['request']
        if value.sponsor != request.user:
            raise serializers.ValidationError('You do not own this property.')
        return value


class LoanRequestListSerializer(serializers.ModelSerializer):
    property_name      = serializers.CharField(source='property.property_name',    read_only=True)
    property_address   = serializers.CharField(source='property.property_address', read_only=True)
    property_type      = serializers.CharField(source='property.property_type',    read_only=True)
    occupancy          = serializers.DecimalField(source='property.occupancy', max_digits=5, decimal_places=2, read_only=True)
    year_built         = serializers.IntegerField(source='property.year_built',    read_only=True)
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = LoanRequest
        fields = [
            'id', 'property', 'property_name', 'property_address',
            'property_type', 'occupancy', 'year_built', 'property_image_url',
            'requested_amount', 'loan_term', 'ltv', 'status', 'created_at',
        ]

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property.property_image and request:
            return request.build_absolute_uri(obj.property.property_image.url)
        return None


class LoanRequestDetailSerializer(serializers.ModelSerializer):
    property_name      = serializers.CharField(source='property.property_name',    read_only=True)
    property_address   = serializers.CharField(source='property.property_address', read_only=True)
    property_type      = serializers.CharField(source='property.property_type',    read_only=True)
    occupancy          = serializers.DecimalField(source='property.occupancy', max_digits=5, decimal_places=2, read_only=True)
    year_built         = serializers.IntegerField(source='property.year_built',    read_only=True)
    property_image_url = serializers.SerializerMethodField()
    memorandum_links   = serializers.SerializerMethodField()
    document_links     = serializers.SerializerMethodField()

    class Meta:
        model  = LoanRequest
        fields = [
            'id', 'property', 'property_name', 'property_address',
            'property_type', 'occupancy', 'year_built', 'property_image_url',
            'requested_amount', 'loan_term', 'ltv', 'status',
            'created_at', 'updated_at',
            'memorandum_links', 'document_links',
        ]

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property.property_image and request:
            return request.build_absolute_uri(obj.property.property_image.url)
        return None

    def get_memorandum_links(self, obj):
        request = self.context.get('request')
        memorandums = obj.property.memorandums.filter(status='Published').values('id', 'title')
        if not request:
            return list(memorandums)
        return [
            {
                'id':    m['id'],
                'title': m['title'],
                'url':   request.build_absolute_uri(f'/api/memorandums/{m["id"]}/'),
            }
            for m in memorandums
        ]

    def get_document_links(self, obj):
        request = self.context.get('request')
        docs = obj.property.documents.all()
        if not request:
            return []
        return [
            {
                'id':  doc.id,
                'url': request.build_absolute_uri(doc.file.url),
            }
            for doc in docs if doc.file
        ]


class LoanRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LoanRequest
        fields = ['requested_amount', 'loan_term', 'ltv', 'status']

    def validate_status(self, value):
        instance = self.instance
        if instance and instance.status == 'Closed':
            raise serializers.ValidationError('Cannot update a closed loan request.')
        return value


def _compute_dscr(quote):
    # DSCR = NOI / Annual Debt Service
    # NOI = loan_amount * min_as_is_dy / 100  (proxy using debt yield)
    # Annual Debt Service = loan_amount * interest_rate / 100
    try:
        loan_amount   = float(quote.loan_amount)
        interest_rate = float(quote.interest_rate)
        min_as_is_dy  = float(quote.min_as_is_dy)
        if interest_rate == 0:
            return None
        noi                 = loan_amount * (min_as_is_dy / 100)
        annual_debt_service = loan_amount * (interest_rate / 100)
        return round(noi / annual_debt_service, 2)
    except (TypeError, ZeroDivisionError):
        return None


class LoanQuoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LoanQuote
        fields = [
            'lender_name', 'guarantor', 'expires_at',
            'loan_amount', 'initial_funding', 'future_funding', 'sponsor_equity',
            'max_as_is_ltv', 'max_ltc', 'max_as_stabilized_ltv',
            'min_as_is_dy', 'min_stabilized_dy',
            'term', 'interest_rate', 'amortization', 'prepayment',
            'origination_fee', 'capex_reserve', 'ff_and_e_reserve', 'interest_carry_reserve',
            'extension_conditions', 'collateral', 'recourse',
        ]


class LoanQuoteSerializer(serializers.ModelSerializer):
    dscr = serializers.SerializerMethodField()

    class Meta:
        model  = LoanQuote
        fields = [
            'id', 'loan_request', 'lender', 'lender_name', 'guarantor',
            'status', 'expires_at', 'submitted_at', 'updated_at',
            'loan_amount', 'initial_funding', 'future_funding', 'sponsor_equity',
            'max_as_is_ltv', 'max_ltc', 'max_as_stabilized_ltv',
            'min_as_is_dy', 'min_stabilized_dy',
            'term', 'interest_rate', 'amortization', 'prepayment',
            'origination_fee', 'capex_reserve', 'ff_and_e_reserve', 'interest_carry_reserve',
            'extension_conditions', 'collateral', 'recourse',
            'dscr',
        ]
        read_only_fields = ['id', 'loan_request', 'lender', 'submitted_at', 'updated_at', 'dscr']

    def get_dscr(self, obj):
        return _compute_dscr(obj)


class LoanQuoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LoanQuote
        fields = [
            'lender_name', 'guarantor', 'expires_at',
            'loan_amount', 'initial_funding', 'future_funding', 'sponsor_equity',
            'max_as_is_ltv', 'max_ltc', 'max_as_stabilized_ltv',
            'min_as_is_dy', 'min_stabilized_dy',
            'term', 'interest_rate', 'amortization', 'prepayment',
            'origination_fee', 'capex_reserve', 'ff_and_e_reserve', 'interest_carry_reserve',
            'extension_conditions', 'collateral', 'recourse',
        ]

    def validate(self, data):
        if self.instance and self.instance.status != 'Submitted':
            raise serializers.ValidationError(
                'Quote can only be updated while status is Submitted.'
            )
        return data


class LenderDashboardRequestSerializer(serializers.ModelSerializer):
    # lightweight loan request card for lender dashboard
    property_name      = serializers.CharField(source='property.property_name',    read_only=True)
    property_address   = serializers.CharField(source='property.property_address', read_only=True)
    property_type      = serializers.CharField(source='property.property_type',    read_only=True)
    occupancy          = serializers.DecimalField(source='property.occupancy', max_digits=5, decimal_places=2, read_only=True)
    year_built         = serializers.IntegerField(source='property.year_built',    read_only=True)
    property_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = LoanRequest
        fields = [
            'id', 'property_name', 'property_address', 'property_type',
            'occupancy', 'year_built', 'property_image_url',
            'requested_amount', 'loan_term', 'ltv',
        ]

    def get_property_image_url(self, obj):
        request = self.context.get('request')
        if obj.property.property_image and request:
            return request.build_absolute_uri(obj.property.property_image.url)
        return None


class SponsorQuoteCardSerializer(serializers.ModelSerializer):
    # lightweight quote card for sponsor dashboard with DSCR comparison
    dscr = serializers.SerializerMethodField()

    class Meta:
        model  = LoanQuote
        fields = [
            'id', 'lender_name', 'loan_amount', 'max_as_is_ltv',
            'interest_rate', 'term', 'origination_fee', 'dscr',
            'expires_at', 'status',
        ]

    def get_dscr(self, obj):
        return _compute_dscr(obj)