from django.urls import path

from .views import (
    FanPortalTournamentOverviewView,
    FanPortalTournamentSubscribeView,
    FanPortalTournamentUnsubscribeView,
    FanPortalProfileView,
)


urlpatterns = [
    path(
        "tournaments/<uuid:tournament_id>/overview/",
        FanPortalTournamentOverviewView.as_view(),
        name="fanportal-tournament-overview",
    ),
    path(
        "tournaments/<uuid:tournament_id>/subscribe/",
        FanPortalTournamentSubscribeView.as_view(),
        name="fanportal-tournament-subscribe",
    ),
    path(
        "tournaments/<uuid:tournament_id>/unsubscribe/",
        FanPortalTournamentUnsubscribeView.as_view(),
        name="fanportal-tournament-unsubscribe",
    ),
    path(
        "me/",
        FanPortalProfileView.as_view(),
        name="fanportal-profile",
    ),
]

