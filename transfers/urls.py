"""
BOLAYETU — Transfers URL Configuration

API endpoints for transfers.

Endpoints:
    GET    /api/v1/transfers/                      — List transfers
    POST   /api/v1/transfers/                      — Create transfer request
    GET    /api/v1/transfers/{id}/                 — Get transfer detail
    POST   /api/v1/transfers/{id}/approve/         — Approve transfer
    POST   /api/v1/transfers/{id}/reject/          — Reject transfer
    POST   /api/v1/transfers/{id}/complete/        — Complete transfer
    POST   /api/v1/transfers/{id}/cancel/          — Cancel transfer
"""

from django.urls import path

from transfers.views import (
    TransferListCreateView,
    TransferDetailView,
    TransferApproveView,
    TransferRejectView,
    TransferCompleteView,
    TransferCancelView,
)

urlpatterns = [
    path("", TransferListCreateView.as_view(), name="transfer-list-create"),
    path("<uuid:transfer_id>/", TransferDetailView.as_view(), name="transfer-detail"),
    path("<uuid:transfer_id>/approve/", TransferApproveView.as_view(), name="transfer-approve"),
    path("<uuid:transfer_id>/reject/", TransferRejectView.as_view(), name="transfer-reject"),
    path("<uuid:transfer_id>/complete/", TransferCompleteView.as_view(), name="transfer-complete"),
    path("<uuid:transfer_id>/cancel/", TransferCancelView.as_view(), name="transfer-cancel"),
]
