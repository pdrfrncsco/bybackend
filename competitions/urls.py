from django.urls import path

from competitions.views import CompetitionListCreateView, CompetitionDetailView

urlpatterns = [
    path("", CompetitionListCreateView.as_view(), name="competition-list-create"),
    path("<uuid:competition_id>/", CompetitionDetailView.as_view(), name="competition-detail"),
]
