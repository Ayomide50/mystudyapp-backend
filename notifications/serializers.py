from rest_framework import serializers
from .models import Notification
from accounts.serializers import CustomUserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'user', 'title', 'message', 'type', 'is_read', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
