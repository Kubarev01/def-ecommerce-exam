from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.profiles.views import ProfileView, ShippingAddressView, ShippingAddressViewId

urlpatterns = [
    path('',ProfileView.as_view(),name="profile"),
    path('shipping_addresses',ShippingAddressView.as_view()),
    path('shipping_addresses/detail/<uuid:id>/',ShippingAddressViewId.as_view()),


]