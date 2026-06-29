"""
BOLAYETU — Standard Pagination

Provides a consistent pagination format across all list endpoints.
All paginated responses use the standard success envelope.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination for all Bolayetu list endpoints.

    Query parameters:
        page (int): Page number (default 1).
        page_size (int): Number of results per page (default 20, max 100).
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data: list) -> Response:
        """Return paginated results within the standard success envelope."""
        return Response(
            {
                "success": True,
                "message": "",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        """OpenAPI schema for paginated responses."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": schema,
                    },
                },
            },
        }
