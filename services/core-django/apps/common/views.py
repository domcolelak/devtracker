from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """USED BY docker-compose HEALTHCHECK AND THE NGINX UPSTREAM CHECK."""
    return JsonResponse({"status": "ok", "service": "core-django"})
