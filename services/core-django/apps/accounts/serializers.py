from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

# THE CONCRETE MODEL CLASS (NOT get_user_model()) SO IT WORKS AS A TYPE
# ANNOTATION - THIS SERVICE OWNS THE USER MODEL, SO THE INDIRECTION THAT
# get_user_model() PROVIDES FOR REUSABLE APPS BUYS NOTHING HERE
from apps.common.models import User
from apps.teams.models import Membership


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "job_title", "avatar_url"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MembershipSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    team_slug = serializers.CharField(source="team.slug", read_only=True)

    class Meta:
        model = Membership
        fields = ["team", "team_name", "team_slug", "role", "joined_at"]
