from typing import cast

from rest_framework import generics, permissions

from apps.common.models import User

from .serializers import MembershipSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """PUBLIC SELF-SERVICE REGISTRATION ENDPOINT."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class MyMembershipsView(generics.ListAPIView):
    """LISTS TEAMS THE AUTHENTICATED USER BELONGS TO, USED BY OTHER SERVICES/CLIENTS
    TO DISCOVER WHICH team_id VALUES A USER MAY OPERATE ON."""

    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # IsAuthenticated GUARANTEES A REAL User HERE, BUT request.user IS TYPED AS
        # User | AnonymousUser - THE cast TELLS MYPY WHAT THE PERMISSION ENFORCES
        user = cast(User, self.request.user)
        return user.memberships.select_related("team")
