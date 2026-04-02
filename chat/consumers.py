import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Get room name from URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("✅ CONNECTED")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("❌ DISCONNECTED")

    async def receive(self, text_data):
        print("📩 RECEIVED:", text_data)

        try:
            data = json.loads(text_data)
        except Exception:
            return  # ignore invalid data

        username = data.get("username", "User")

        # =========================
        # 1️⃣ Typing Event
        # =========================
        if "typing" in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "username": username,
                    "typing": data["typing"]
                }
            )
            return

        # =========================
        # 2️⃣ Seen Event
        # =========================
        if "seen" in data:
            message_id = data.get("message_id")

            if not message_id:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "seen_status",
                    "message_id": message_id,
                    "seen_by": username
                }
            )
            return

        # =========================
        # 3️⃣ Message Event
        # =========================
        message = data.get("message")

        if not message:
            return

        message_id = str(uuid.uuid4())

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": username,
                "message_id": message_id
            }
        )

    # =========================
    # Send message to clients
    # =========================
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender": event["sender"],
            "message_id": event["message_id"]
        }))

    # =========================
    # Typing status
    # =========================
    async def typing_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": event["username"],
            "typing": event["typing"]
        }))

    # =========================
    # Seen status
    # =========================
    async def seen_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "seen",
            "message_id": event["message_id"],
            "seen_by": event["seen_by"]
        }))