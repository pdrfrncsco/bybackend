"""
BOLAYETU — Analytics Constants

Formalizes metric types, report types, statuses and formats.
"""

class MetricKey:
    TOTAL_CLUBS = "total_clubs"
    TOTAL_PLAYERS = "total_players"
    ACTIVE_TOURNAMENTS = "active_tournaments"
    TOTAL_MATCHES = "total_matches"
    MATCHES_FINISHED = "matches_finished"
    MATCHES_SCHEDULED = "matches_scheduled"
    MATCHES_LIVE = "matches_live"
    GOALS_TOTAL = "goals_total"
    AVG_GOALS_PER_MATCH = "avg_goals_per_match"
    ORGANIZATION_SUBSCRIBERS = "organization_subscribers"
    TOTAL_REVENUE = "total_revenue"
    PLAYERS_THIS_MONTH = "players_this_month"
    PLAYERS_LAST_MONTH = "players_last_month"

    CHOICES = [
        (TOTAL_CLUBS, "Total Clubs"),
        (TOTAL_PLAYERS, "Total Players"),
        (ACTIVE_TOURNAMENTS, "Active Tournaments"),
        (TOTAL_MATCHES, "Total Matches"),
        (MATCHES_FINISHED, "Matches Finished"),
        (MATCHES_SCHEDULED, "Matches Scheduled"),
        (MATCHES_LIVE, "Matches Live"),
        (GOALS_TOTAL, "Goals Total"),
        (AVG_GOALS_PER_MATCH, "Average Goals Per Match"),
        (ORGANIZATION_SUBSCRIBERS, "Organization Subscribers"),
        (TOTAL_REVENUE, "Total Revenue"),
        (PLAYERS_THIS_MONTH, "Players Joined This Month"),
        (PLAYERS_LAST_MONTH, "Players Joined Last Month"),
    ]


class ReportType:
    CLUB_OVERVIEW = "club_overview"
    COMPETITION_SUMMARY = "competition_summary"
    ORGANIZATION_PERFORMANCE = "organization_performance"
    FINANCIAL_SUMMARY = "financial_summary"

    CHOICES = [
        (CLUB_OVERVIEW, "Club Overview"),
        (COMPETITION_SUMMARY, "Competition Summary"),
        (ORGANIZATION_PERFORMANCE, "Organization Performance Summary"),
        (FINANCIAL_SUMMARY, "Financial Summary"),
    ]


class ReportStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]


class ReportFormat:
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"

    CHOICES = [
        (CSV, "CSV"),
        (XLSX, "Excel (XLSX)"),
        (PDF, "PDF"),
    ]
