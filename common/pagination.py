"""
BOLAYETU — Common Pagination
Standard paginator for all Bolayetu API endpoints.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Default paginator for all list endpoints.

    Usage in ViewSet:
        pagination_class = StandardResultsPagination

    Response format:
        {
            "count": 100,
            "totalPages": 5,
            "currentPage": 1,
            "next": "https://api.../clubs/?page=2",
            "previous": null,
            "results": [...]
        }
    """
    page_size = 20
    page_size_query_param = 'pageSize'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'totalPages': self.page.paginator.num_pages,
            'currentPage': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer', 'example': 100},
                'totalPages': {'type': 'integer', 'example': 5},
                'currentPage': {'type': 'integer', 'example': 1},
                'next': {'type': 'string', 'nullable': True},
                'previous': {'type': 'string', 'nullable': True},
                'results': schema,
            },
        }


class LargeResultsPagination(PageNumberPagination):
    """For endpoints that need larger page sizes (e.g., rankings, stats)."""
    page_size = 50
    page_size_query_param = 'pageSize'
    max_page_size = 200
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'totalPages': self.page.paginator.num_pages,
            'currentPage': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
