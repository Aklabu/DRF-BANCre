from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from properties.models import Property, PropertyChatSession, PropertyChatMessage

User = get_user_model()


class PropertyChatTests(APITestCase):
    def setUp(self):
        # Create users
        self.sponsor = User.objects.create_user(
            email='sponsor@example.com',
            password='password123',
            customer_type='Sponsor',
            first_name='John',
            last_name='Doe'
        )
        self.lender = User.objects.create_user(
            email='lender@example.com',
            password='password123',
            customer_type='Lender',
            first_name='Jane',
            last_name='Smith'
        )

        # Create a property owned by the sponsor
        self.property = Property.objects.create(
            latitude=40.7128,
            longitude=-74.0060,
            property_name='Central Park Tower',
            property_address='225 W 57th St, New York, NY 10019',
            property_type='Multifamily',
            number_of_units=179,
            rentable_area=50000.00,
            year_built=2020,
            occupancy=95.00,
            parking_spaces=100,
            sponsor=self.sponsor
        )

    def test_unauthenticated_access_denied(self):
        url = reverse('properties:property-chat-session-list-create', kwargs={'pk': self.property.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_and_create_sessions(self):
        self.client.force_authenticate(user=self.lender)
        list_url = reverse('properties:property-chat-session-list-create', kwargs={'pk': self.property.pk})

        # List initially empty
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)

        # Create session
        response = self.client.post(list_url, {'title': 'My Chat Session'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'My Chat Session')
        session_id = response.data['data']['id']

        # List again, should have 1 session
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], session_id)

    @patch('properties.views.ask')
    def test_chat_without_session_creates_session(self, mock_ask):
        mock_ask.return_value = 'Mock reply from AI'
        self.client.force_authenticate(user=self.lender)

        chat_url = reverse('properties:property-chat', kwargs={'pk': self.property.pk})
        
        # Post a message without session_id
        response = self.client.post(chat_url, {'message': 'Hello, tell me about this property'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['reply'], 'Mock reply from AI')
        self.assertIn('session_id', response.data['data'])
        session_id = response.data['data']['session_id']

        # Verify session and messages are persisted in DB
        session = PropertyChatSession.objects.get(id=session_id)
        self.assertEqual(session.title, 'Hello, tell me about this property')
        self.assertEqual(session.messages.count(), 2)  # 1 user message, 1 assistant reply
        self.assertEqual(session.messages.first().role, 'user')
        self.assertEqual(session.messages.first().content, 'Hello, tell me about this property')
        self.assertEqual(session.messages.last().role, 'assistant')
        self.assertEqual(session.messages.last().content, 'Mock reply from AI')

    @patch('properties.views.ask')
    def test_chat_with_existing_session(self, mock_ask):
        mock_ask.return_value = 'Follow-up reply'
        self.client.force_authenticate(user=self.lender)

        # Pre-create session
        session = PropertyChatSession.objects.create(
            property=self.property,
            user=self.lender,
            title='Ongoing Discussion'
        )
        PropertyChatMessage.objects.create(
            session=session,
            role='user',
            content='First question'
        )
        PropertyChatMessage.objects.create(
            session=session,
            role='assistant',
            content='First answer'
        )

        chat_url = reverse('properties:property-chat', kwargs={'pk': self.property.pk})
        response = self.client.post(chat_url, {
            'message': 'Second question',
            'session_id': session.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['reply'], 'Follow-up reply')
        self.assertEqual(response.data['data']['session_id'], session.id)

        # Check call args of mock_ask: should include history
        mock_ask.assert_called_once_with(
            self.property.id,
            'Second question',
            [{'role': 'user', 'content': 'First question'}, {'role': 'assistant', 'content': 'First answer'}]
        )

        # Verify DB counts
        self.assertEqual(session.messages.count(), 4)

    def test_retrieve_session_messages_and_delete(self):
        self.client.force_authenticate(user=self.lender)
        session = PropertyChatSession.objects.create(
            property=self.property,
            user=self.lender,
            title='Test Session'
        )
        msg = PropertyChatMessage.objects.create(
            session=session,
            role='user',
            content='Hi'
        )

        detail_url = reverse('properties:property-chat-session-detail', kwargs={
            'pk': self.property.pk,
            'session_id': session.id
        })

        # Get messages
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['content'], 'Hi')

        # Try to access with a different user
        self.client.force_authenticate(user=self.sponsor)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Delete with owner
        self.client.force_authenticate(user=self.lender)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify gone
        self.assertFalse(PropertyChatSession.objects.filter(id=session.id).exists())
