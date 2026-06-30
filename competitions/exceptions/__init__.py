class CompetitionNotFound(Exception):
    """Raised when a competition cannot be found."""


class DuplicateCompetition(Exception):
    """Raised when a competition with the same name/season already exists."""
