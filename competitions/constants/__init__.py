class CompetitionType:
    LEAGUE = "league"
    TOURNAMENT = "tournament"
    CUP = "cup"

    CHOICES = [
        (LEAGUE, "Liga"),
        (TOURNAMENT, "Torneio"),
        (CUP, "Taça"),
    ]

    LABELS = {
        LEAGUE: "Liga",
        TOURNAMENT: "Torneio",
        CUP: "Taça",
    }


class CompetitionStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    INACTIVE = "inactive"

    CHOICES = [
        (DRAFT, "Rascunho"),
        (ACTIVE, "Ativa"),
        (COMPLETED, "Concluída"),
        (INACTIVE, "Inativa"),
    ]

    LABELS = {
        DRAFT: "Rascunho",
        ACTIVE: "Ativa",
        COMPLETED: "Concluída",
        INACTIVE: "Inativa",
    }

