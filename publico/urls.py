from django.urls import path

from .views import AdvertiseContactView, SupportContactView


urlpatterns = [
    path("contact/advertise/", AdvertiseContactView.as_view(), name="public-contact-advertise"),
    path("contact/support/", SupportContactView.as_view(), name="public-contact-support"),
]
