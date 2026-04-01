import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Conversation, Message, Customer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @sync_to_async
    def get_conversation(self, conversation_id):
        return Conversation.objects.select_related('user1', 'user2').get(id=conversation_id)

    @sync_to_async
    def create_message(self, conversation, sender, content):
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )

    @sync_to_async
    def get_customer_by_id(self, customer_id):
        return Customer.objects.get(id=customer_id)

    async def receive(self, text_data):
        print("\n====== receive() CALLED ======")
        print("Raw WebSocket data received:", text_data)

        try:
            data = json.loads(text_data)
            content = data.get('content', '').strip()
            print("Parsed content:", content)
        except Exception as e:
            print("❌ Failed to parse JSON:", e)
            await self.send(text_data=json.dumps({'error': 'Invalid JSON'}))
            return

        user = self.scope.get('user')
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            print("❌ User not authenticated.")
            await self.send(text_data=json.dumps({'error': 'Authentication required'}))
            return

        # ✅ استرجاع كائن Customer الفعلي من قاعدة البيانات
        try:
            customer = await self.get_customer_by_id(user.id)
        except Customer.DoesNotExist:
            print("❌ Authenticated user not found in database")
            await self.send(text_data=json.dumps({'error': 'Invalid user'}))
            return

        print(f"✅ Authenticated Customer: ID={customer.id}, Email={customer.email}")

        # ✅ جلب المحادثة
        try:
            conversation = await self.get_conversation(self.conversation_id)
            print(f"✅ Conversation loaded between user1={conversation.user1_id} and user2={conversation.user2_id}")
        except Conversation.DoesNotExist:
            await self.send(text_data=json.dumps({'error': 'Conversation not found'}))
            return

        # ✅ التحقق من أن المستخدم طرف في المحادثة
        if customer.id not in [conversation.user1_id, conversation.user2_id]:
            print(f"❌ Customer {customer.id} not part of the conversation")
            await self.send(text_data=json.dumps({'error': 'Access denied to this conversation'}))
            return

        try:
            msg = await self.create_message(conversation, customer, content)
            print("✅ Message saved:", msg)
        except Exception as e:
            print("❌ Error while saving message:", e)
            await self.send(text_data=json.dumps({'error': 'Failed to save message'}))
            return

        # ✅ بث الرسالة للجميع في الغرفة
        message_data = {
            'id': msg.id,
            'content': msg.content,
            'sender_id': customer.id,
            'created_at': msg.sent_at.isoformat(),
        }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
