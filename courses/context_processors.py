from .models import HomePageSettings


def homepage_settings(request):
    settings, _ = HomePageSettings.objects.get_or_create(pk=1)
    return {"home_settings": settings}
