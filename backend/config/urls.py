from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

def home_view(request):
    return HttpResponse("My app is running successfully!")

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/account/', include('apps.account.urls')),
    path('api/agrovet/', include('apps.agrovet.urls')),
    path('accounts/', include('rest_framework.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from django.conf.urls.static import static
# from django.urls import path, include

# urlpatterns = [
#     # Your other URLs
#     path('api/', include('your_app.urls')),
# ]

