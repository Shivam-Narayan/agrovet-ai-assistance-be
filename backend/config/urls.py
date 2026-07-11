from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Agrovet API",
        default_version='v1',
        description="Core API endpoints for user authentication, animal disease prediction, and activity tracking.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url='http://localhost:8000/',
)

from django.http import HttpResponse

def home_view(request):
    return HttpResponse("My app is running successfully!")

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/account/', include('apps.account.urls')),
    path('api/agrovet/', include('apps.agrovet.urls')),
    path('accounts/', include('rest_framework.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from django.conf.urls.static import static
# from django.urls import path, include

# urlpatterns = [
#     # Your other URLs
#     path('api/', include('your_app.urls')),
# ]

