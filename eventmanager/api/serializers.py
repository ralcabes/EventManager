from events.models import Event
from events.models import Comment
from events.models import Invite
from categories.models import Category
from accounts.models import AccountDetails

from rest_framework import serializers


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "title",
            "description",
            "category",
            "attendees",
            "team_members",
            "cover_image",
            "added_by",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at"
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at"
        )


class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "title", "author", "content", "event",)


class InvitationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ("id", "invited_user", "invited_by", "event", "is_accepted",)


class AccountDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountDetails
        fields = (
            "user",
            "profile_picture",
            "friends",
            "birth_date",
            "description",
        )