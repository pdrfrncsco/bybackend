from rest_framework import status
from rest_framework.exceptions import APIException


class CompetitionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A competitions error occurred."
    default_code = "competitions_error"


class CompetitionNotFound(CompetitionException):
    """Raised when a competition cannot be found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Competition not found."
    default_code = "competition_not_found"


class DuplicateCompetition(CompetitionException):
    """Raised when a competition with the same name/season already exists."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A competition with this name and season already exists."
    default_code = "duplicate_competition"


class DuplicateCompetitionRegulation(CompetitionException):
    """Raised when a competition regulation with the same version exists."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A regulation with this title and version already exists."
    default_code = "duplicate_competition_regulation"
