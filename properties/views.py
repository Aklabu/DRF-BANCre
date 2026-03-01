from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from utils.response import CustomResponse
from .models import Property, PropertyDocument
from .serializers import (
    PropertySerializer, PropertyListSerializer,
    PropertyDocumentSerializer, PropertyMapSerializer,
)
from .permissions import IsSponsor, IsLender, IsPropertyOwner
from .validators import validate_documents


class PropertyListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def get(self, request):
        properties = Property.objects.filter(sponsor=request.user)
        serializer = PropertyListSerializer(properties, many=True, context={'request': request})
        return CustomResponse.success(message='Properties retrieved successfully.', data=serializer.data)

    def post(self, request):
        serializer = PropertySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(sponsor=request.user)
            return CustomResponse.success(
                message='Property created successfully.',
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        return CustomResponse.error(message='Property creation failed.', errors=serializer.errors, status_code=400)


class PropertyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def _get_property(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        if not IsPropertyOwner().has_object_permission(request, self, prop):
            return None, CustomResponse.error(message='You do not have permission to access this property.', status_code=403)
        return prop, None

    def get(self, request, pk):
        prop, error = self._get_property(request, pk)
        if error:
            return error
        serializer = PropertySerializer(prop, context={'request': request})
        return CustomResponse.success(message='Property retrieved successfully.', data=serializer.data)

    def patch(self, request, pk):
        prop, error = self._get_property(request, pk)
        if error:
            return error
        serializer = PropertySerializer(prop, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message='Property updated successfully.', data=serializer.data)
        return CustomResponse.error(message='Property update failed.', errors=serializer.errors, status_code=400)

    def delete(self, request, pk):
        prop, error = self._get_property(request, pk)
        if error:
            return error
        prop.delete()
        return CustomResponse.success(message='Property deleted successfully.')


class PropertyDocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def _get_property(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        if not IsPropertyOwner().has_object_permission(request, self, prop):
            return None, CustomResponse.error(message='You do not have permission to access this property.', status_code=403)
        return prop, None

    def get(self, request, pk):
        prop, error = self._get_property(request, pk)
        if error:
            return error
        serializer = PropertyDocumentSerializer(prop.documents.all(), many=True, context={'request': request})
        return CustomResponse.success(message='Documents retrieved successfully.', data=serializer.data)

    def post(self, request, pk):
        prop, error = self._get_property(request, pk)
        if error:
            return error

        files = request.FILES.getlist('files')
        if not files:
            return CustomResponse.error(message="No files provided. Use the 'files' key.", status_code=400)

        valid_files, file_errors = validate_documents(files)
        if file_errors:
            return CustomResponse.error(
                message='One or more files failed validation. No files were saved.',
                errors=file_errors,
                status_code=400,
            )

        docs = [PropertyDocument.objects.create(property=prop, file=f) for f in valid_files]
        serializer = PropertyDocumentSerializer(docs, many=True, context={'request': request})
        return CustomResponse.success(
            message=f'{len(docs)} document(s) uploaded successfully.',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class PropertyDocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def delete(self, request, pk, doc_id):
        prop = get_object_or_404(Property, pk=pk)
        if not IsPropertyOwner().has_object_permission(request, self, prop):
            return CustomResponse.error(message='You do not have permission to access this property.', status_code=403)
        doc = get_object_or_404(PropertyDocument, pk=doc_id, property=prop)
        doc.delete()
        return CustomResponse.success(message='Document deleted successfully.')


class PropertyMapView(APIView):
    # Returns all properties for the lender map
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        properties = Property.objects.only('id', 'property_name', 'property_address', 'property_type', 'latitude', 'longitude')
        serializer = PropertyMapSerializer(properties, many=True, context={'request': request})
        return CustomResponse.success(message='Properties retrieved successfully.', data=serializer.data)