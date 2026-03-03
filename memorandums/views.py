import os
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from utils.response import CustomResponse
from properties.models import Property

from .models import Memorandum, MemorandumSection
from .serializers import (
    GenerateMemorandumSerializer,
    MemorandumListSerializer,
    MemorandumDetailSerializer,
    MemorandumUpdateSerializer,
    MemorandumSectionUpdateSerializer,
    SectionImageSerializer,
)
from .permissions import IsSponsor, IsMemorandumOwner
from .tasks import generate_memorandum_task


# Helper functions to fetch memorandum and section
def _get_memorandum(request, pk) -> tuple:
    memorandum = get_object_or_404(Memorandum, pk=pk)
    if not IsMemorandumOwner().has_object_permission(request, None, memorandum):
        return None, CustomResponse.error(
            message='You do not have permission to access this memorandum.',
            status_code=403,
        )
    return memorandum, None


# Helper function to fetch a section that belongs to a memorandum
def _get_section(memorandum, section_id) -> tuple:
    # Ensure the section belongs to this memorandum
    section = get_object_or_404(MemorandumSection, pk=section_id, memorandum=memorandum)
    return section, None


# generate memorandum based on property data, with sections
class GenerateMemorandumView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def post(self, request):
        serializer = GenerateMemorandumSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Invalid request.',
                errors=serializer.errors,
                status_code=400,
            )

        property_id = serializer.validated_data['property_id']
        prop = get_object_or_404(Property, pk=property_id)

        # Ensure the sponsor owns this property
        if prop.sponsor != request.user:
            return CustomResponse.error(
                message='You do not have permission to generate a memorandum for this property.',
                status_code=403,
            )

        # Create the memorandum record immediately
        memorandum = Memorandum.objects.create(
            property=prop,
            sponsor=request.user,
            title=f'{prop.property_name} — Offering Memorandum',
            status='Generating',
            mode='Editor',
        )

        # Dispatch the background task
        generate_memorandum_task.delay(memorandum.id)

        return CustomResponse.success(
            message='Memorandum generation started.',
            data={'memorandum_id': memorandum.id},
            status_code=status.HTTP_201_CREATED,
        )


# list and detail views for memorandum
class MemorandumListView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def get(self, request):
        memorandums = Memorandum.objects.filter(sponsor=request.user)
        serializer  = MemorandumListSerializer(memorandums, many=True, context={'request': request})
        return CustomResponse.success(
            message='Memorandums retrieved successfully.',
            data=serializer.data,
        )


# detail view with update and delete options for memorandum
class MemorandumDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def get(self, request, pk):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        serializer = MemorandumDetailSerializer(memorandum, context={'request': request})
        return CustomResponse.success(
            message='Memorandum retrieved successfully.',
            data=serializer.data,
        )

    def patch(self, request, pk):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        serializer = MemorandumUpdateSerializer(memorandum, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(
                message='Memorandum updated successfully.',
                data=serializer.data,
            )
        return CustomResponse.error(
            message='Memorandum update failed.',
            errors=serializer.errors,
            status_code=400,
        )

    def delete(self, request, pk):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        memorandum.delete()
        return CustomResponse.success(message='Memorandum deleted successfully.')


# Update a single section's content or image of the memorandum
class MemorandumSectionUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def patch(self, request, pk, section_id):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        section, error = _get_section(memorandum, section_id)
        if error:
            return error

        serializer = MemorandumSectionUpdateSerializer(section, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(
                message='Section updated successfully.',
                data=serializer.data,
            )
        return CustomResponse.error(
            message='Section update failed.',
            errors=serializer.errors,
            status_code=400,
        )


# Upload or delete image for a section of the memorandum
class SectionImageView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def post(self, request, pk, section_id):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        section, error = _get_section(memorandum, section_id)
        if error:
            return error

        serializer = SectionImageSerializer(section, data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Image upload failed.',
                errors=serializer.errors,
                status_code=400,
            )

        # Delete the existing image file from disk before replacing
        if section.image:
            if os.path.isfile(section.image.path):
                os.remove(section.image.path)
            section.image = None
            section.save(update_fields=['image'])

        serializer.save()

        return CustomResponse.success(
            message='Section image uploaded successfully.',
            data=SectionImageSerializer(section, context={'request': request}).data,
            status_code=status.HTTP_201_CREATED,
        )

    def delete(self, request, pk, section_id):
        memorandum, error = _get_memorandum(request, pk)
        if error:
            return error
        section, error = _get_section(memorandum, section_id)
        if error:
            return error

        if not section.image:
            return CustomResponse.error(
                message='This section has no image to delete.',
                status_code=404,
            )

        if os.path.isfile(section.image.path):
            os.remove(section.image.path)
        section.image = None
        section.save(update_fields=['image'])

        return CustomResponse.success(message='Section image deleted successfully.')