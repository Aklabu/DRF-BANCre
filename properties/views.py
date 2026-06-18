from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from utils.response import CustomResponse
from .models import Property, PropertyDocument, PropertyChatSession, PropertyChatMessage
from .serializers import (
    PropertySerializer, PropertyListSerializer,
    PropertyDocumentSerializer, PropertyMapSerializer,
    PropertyChatSessionSerializer, PropertyChatMessageSerializer, PropertyChatInputSerializer,
    PlaceSerializer,
)
from .permissions import IsSponsor, IsLender, IsPropertyOwner
from .validators import validate_documents
from .chatbot import ask


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


class PropertyChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        
        serializer = PropertyChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Invalid request.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_message = serializer.validated_data['message']
        session_id   = serializer.validated_data.get('session_id')

        # --- Resolve or create session ---
        if session_id:
            session = get_object_or_404(PropertyChatSession, pk=session_id, property=prop)
            if session.user != request.user:
                return CustomResponse.error(
                    message='You do not have permission to access this chat session.',
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            is_new = False
        else:
            session = PropertyChatSession.objects.create(property=prop, user=request.user)
            is_new  = True

        is_first_message = is_new or not session.messages.exists()

        # Build history from all existing messages (oldest first)
        existing_messages    = session.messages.order_by('created_at')
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in existing_messages
        ]

        # Persist the user message
        PropertyChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message,
        )

        try:
            reply = ask(prop.id, user_message, conversation_history)
        except Exception:
            return CustomResponse.error(
                message='AI service is temporarily unavailable. Please try again.',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Persist the assistant reply
        PropertyChatMessage.objects.create(
            session=session,
            role='assistant',
            content=reply,
        )

        # Auto-set title from the first 60 chars of the opening message
        if is_first_message:
            session.title = user_message[:60].strip()

        # Touch updated_at on every exchange
        session.save(update_fields=['title', 'updated_at'])

        return CustomResponse.success(
            message='Message sent successfully.',
            data={
                'session_id': session.id,
                'reply':      reply,
            },
            status_code=status.HTTP_201_CREATED,
        )


class PropertyChatSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        prop     = get_object_or_404(Property, pk=pk)
        sessions = PropertyChatSession.objects.filter(property=prop, user=request.user)
        serializer = PropertyChatSessionSerializer(sessions, many=True)
        return CustomResponse.success(
            message='Chat sessions retrieved successfully.',
            data=serializer.data,
        )

    def post(self, request, pk):
        prop  = get_object_or_404(Property, pk=pk)
        title = request.data.get('title', '').strip()
        session = PropertyChatSession.objects.create(
            property=prop,
            user=request.user,
            title=title or "New Chat"
        )
        serializer = PropertyChatSessionSerializer(session)
        return CustomResponse.success(
            message='Chat session created successfully.',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class PropertyChatSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_session(self, request, pk, session_id):
        prop    = get_object_or_404(Property, pk=pk)
        session = get_object_or_404(PropertyChatSession, pk=session_id, property=prop)
        if session.user != request.user:
            return None, CustomResponse.error(
                message='You do not have permission to access this chat session.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return session, None

    def get(self, request, pk, session_id):
        session, error = self._get_session(request, pk, session_id)
        if error:
            return error

        messages   = session.messages.order_by('created_at')
        serializer = PropertyChatMessageSerializer(messages, many=True)
        return CustomResponse.success(
            message='Messages retrieved successfully.',
            data=serializer.data,
        )

    def delete(self, request, pk, session_id):
        session, error = self._get_session(request, pk, session_id)
        if error:
            return error

        session.delete()
        return CustomResponse.success(message='Chat session deleted successfully.')


class PlaceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Invalid place data.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return CustomResponse.success(
            message='Place data received successfully.',
            data=serializer.validated_data,
            status_code=status.HTTP_201_CREATED,
        )
