"""
BOLAYETU — Players Admin

Comprehensive admin interface for all phases of the Player module:
- Phase 1-2: Player, Registration, Documents, Videos, Achievements
- Phase 3: Contracts, Agents, Training History
- Phase 4: Medical Data, National Team, Performance, Compliance

Privacy Note: Medical and financial data access should be restricted
via Django group permissions.
"""

from django.contrib import admin
from django.utils.html import format_html, mark_safe

from players.models import (
    # Phase 1-2
    Player,
    PlayerRegistration,
    PlayerRegistrationRequest,
    PlayerVideo,
    PlayerDocument,
    PlayerAchievement,
    PlayerContact,
    EmergencyContact,
    PlayerIdentityDocument,
    LegalGuardian,
    PlayerExternalId,
    PlayerFootballProfile,
    PlayerCareer,
    PlayerPrivacySettings,
    PlayerInvite,
    # Phase 3
    PlayerContract,
    Agent,
    PlayerAgentRelationship,
    PlayerTrainingHistory,
    # Phase 4
    PlayerMedicalProfile,
    MedicalDocument,
    NationalTeamCallUp,
    PlayerPerformanceMetric,
    PlayerComplianceRecord,
)


# ============================================================================
# PHASE 1-2 INLINES
# ============================================================================

class PlayerRegistrationInline(admin.TabularInline):
    model = PlayerRegistration
    extra = 0
    raw_id_fields = ("club", "competition", "tenant")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = (
        "club",
        "competition",
        "tenant",
        "shirt_number",
        "joined_date",
        "left_date",
        "status",
        "matches_played",
        "goals",
        "assists",
    )


class PlayerVideoInline(admin.TabularInline):
    model = PlayerVideo
    extra = 0
    raw_id_fields = ("media_asset", "match")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = ("title", "video_type", "status", "media_asset", "is_featured", "created_at")


class PlayerDocumentInline(admin.TabularInline):
    model = PlayerDocument
    extra = 0
    raw_id_fields = ("asset", "club", "uploaded_by")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    fields = ("title", "category", "status", "asset", "club", "is_private", "created_at")


class PlayerAchievementInline(admin.TabularInline):
    model = PlayerAchievement
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")
    fields = ("achievement_type", "title", "description", "date_achieved", "created_at")


# ============================================================================
# PHASE 3 INLINES
# ============================================================================

class PlayerContractInline(admin.TabularInline):
    model = PlayerContract
    extra = 0
    raw_id_fields = ("club", "contract_document", "verified_by")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = (
        "contract_type",
        "club",
        "status",
        "start_date",
        "end_date",
        "salary",
        "currency",
        "signed_by_player",
        "signed_by_club",
    )


class PlayerAgentRelationshipInline(admin.TabularInline):
    model = PlayerAgentRelationship
    extra = 0
    raw_id_fields = ("agent", "representation_agreement")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = (
        "agent",
        "status",
        "start_date",
        "end_date",
        "commission_rate",
    )


class PlayerTrainingHistoryInline(admin.TabularInline):
    model = PlayerTrainingHistory
    extra = 0
    raw_id_fields = ("club", "verified_by")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    fields = (
        "academy_name",
        "club",
        "country",
        "training_category",
        "start_date",
        "end_date",
        "verified",
    )


# ============================================================================
# PHASE 4 INLINES
# ============================================================================

class MedicalDocumentInline(admin.TabularInline):
    """Inline for medical documents within Player admin (FK to Player)."""
    model = MedicalDocument
    extra = 0
    raw_id_fields = ("file", "verified_by")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    fields = (
        "document_type",
        "title",
        "issued_at",
        "expires_at",
        "verification_status",
        "is_confidential",
    )


class NationalTeamCallUpInline(admin.TabularInline):
    model = NationalTeamCallUp
    extra = 0
    raw_id_fields = ("competition",)
    readonly_fields = ("id", "created_at", "updated_at")
    fields = (
        "national_team",
        "category",
        "competition",
        "call_up_date",
        "release_date",
        "status",
        "caps",
    )


# ============================================================================
# PHASE 1-2 ADMIN CLASSES
# ============================================================================

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Main Player admin — master view for all phases."""

    list_display = (
        "full_name",
        "global_id_display",
        "primary_position",
        "status",
        "nationality",
        "user",
        "active_contract_display",
    )
    list_filter = ("status", "primary_position", "nationality", "foot", "created_at")
    search_fields = ("first_name", "last_name", "slug", "global_id")
    readonly_fields = (
        "id",
        "slug",
        "global_id",
        "created_at",
        "updated_at",
        "total_matches",
        "total_goals",
        "total_assists",
        "profile_photo_url",
    )
    raw_id_fields = ("user", "profile_photo")
    inlines = (
        # Phase 1-2
        PlayerRegistrationInline,
        PlayerVideoInline,
        PlayerDocumentInline,
        PlayerAchievementInline,
        # Phase 3
        PlayerContractInline,
        PlayerAgentRelationshipInline,
        PlayerTrainingHistoryInline,
        # Phase 4
        NationalTeamCallUpInline,
        MedicalDocumentInline,
    )
    fieldsets = (
        (
            "🆔 Global Identity",
            {
                "fields": (
                    "global_id",
                    "id",
                    "first_name",
                    "last_name",
                    "slug",
                )
            },
        ),
        (
            "👤 Personal Information",
            {
                "fields": (
                    "date_of_birth",
                    "nationality",
                    "height_cm",
                    "weight_kg",
                    "foot",
                )
            },
        ),
        (
            "📞 Contact (DEPRECATED — use PlayerContact model)",
            {
                "fields": (
                    "email",
                    "phone",
                ),
                "description": "⚠️ DEPRECATED: Use PlayerContact model instead.",
                "classes": ("collapse",),
            },
        ),
        (
            "⚽ Football Profile",
            {
                "fields": (
                    "primary_position",
                    "shirt_number",
                )
            },
        ),
        (
            "📸 Media & Profile",
            {
                "fields": (
                    "bio",
                    "profile_photo",
                    "profile_photo_url",
                    "avatar",
                ),
                "description": "Use 'profile_photo' for new uploads. 'avatar' is deprecated.",
                "classes": ("collapse",),
            },
        ),
        (
            "📊 Career Statistics",
            {
                "fields": (
                    "total_matches",
                    "total_goals",
                    "total_assists",
                )
            },
        ),
        (
            "🔐 Status & Account",
            {
                "fields": (
                    "status",
                    "is_public",
                    "user",
                )
            },
        ),
        (
            "📅 Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def global_id_display(self, obj):
        if obj.global_id:
            return format_html(
                '<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;">{}</code>',
                obj.global_id,
            )
        return "—"
    global_id_display.short_description = "Global ID"

    def active_contract_display(self, obj):
        contract = obj.contracts.filter(status="active").first()
        if contract:
            return format_html(
                '<span style="color:green;font-weight:bold;">✓ {}</span>',
                contract.club.name,
            )
        return mark_safe('<span style="color:gray;">—</span>')
    active_contract_display.short_description = "Contrato Ativo"


@admin.register(PlayerRegistration)
class PlayerRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "player", "club", "competition", "tenant",
        "shirt_number", "joined_date", "left_date", "status",
    )
    list_filter = ("status", "tenant", "joined_date")
    search_fields = (
        "player__first_name", "player__last_name",
        "club__name", "competition__name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "club", "competition", "tenant")
    date_hierarchy = "joined_date"
    fieldsets = (
        ("Registration", {"fields": ("player", "club", "competition", "tenant")}),
        ("Details", {"fields": ("shirt_number", "joined_date", "left_date", "status")}),
        ("Statistics", {"fields": ("matches_played", "goals", "assists", "yellow_cards", "red_cards")}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(PlayerRegistrationRequest)
class PlayerRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("player", "club", "status", "joined_date", "submitted_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("player__first_name", "player__last_name", "club__name")
    readonly_fields = ("id", "created_at", "updated_at", "reviewed_at")
    raw_id_fields = (
        "player", "club", "tenant", "competition",
        "submitted_by", "reviewed_by", "registration",
    )


@admin.register(PlayerVideo)
class PlayerVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "video_type", "status", "is_featured", "created_at")
    list_filter = ("video_type", "status", "is_featured", "created_at")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "media_asset", "match")


@admin.register(PlayerDocument)
class PlayerDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "category", "status", "uploaded_by", "created_at")
    list_filter = ("category", "status", "is_private", "created_at")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    raw_id_fields = ("player", "asset", "club", "uploaded_by", "verified_by")


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "achievement_type", "level", "date_achieved")
    list_filter = ("achievement_type", "level", "date_achieved")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "competition", "club")


# ============================================================================
# PHASE 3 ADMIN CLASSES
# ============================================================================

@admin.register(PlayerContract)
class PlayerContractAdmin(admin.ModelAdmin):
    """
    Admin for PlayerContract.
    ⚠️ RESTRICTED: Salary and financial terms visible only to authorized personnel.
    """

    list_display = (
        "player_name",
        "club_name",
        "contract_type",
        "status",
        "start_date",
        "end_date",
        "salary_display",
        "signatures_display",
    )
    list_filter = (
        "status", "contract_type",
        "signed_by_player", "signed_by_club",
        "created_at",
    )
    search_fields = ("player__first_name", "player__last_name", "club__name")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    raw_id_fields = ("player", "club", "tenant", "contract_document", "verified_by")
    date_hierarchy = "start_date"
    fieldsets = (
        (
            "📋 Contract",
            {"fields": ("player", "club", "contract_type", "status")},
        ),
        (
            "📅 Period",
            {"fields": ("start_date", "end_date", "signed_date")},
        ),
        (
            "💰 Financial Terms (Restricted)",
            {
                "fields": ("salary", "currency", "bonuses", "release_clause"),
                "description": "⚠️ RESTRICTED: Visible only to authorized personnel.",
            },
        ),
        (
            "📜 Clauses",
            {"fields": ("has_image_rights", "option_year", "termination_clause")},
        ),
        (
            "✍️ Signatures",
            {"fields": ("signed_by_player", "signed_by_club", "verified_by", "verified_at")},
        ),
        (
            "📄 Document",
            {"fields": ("contract_document",)},
        ),
        (
            "🏢 Organisation",
            {"fields": ("tenant",), "classes": ("collapse",)},
        ),
        (
            "📊 Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def club_name(self, obj):
        return obj.club.name
    club_name.short_description = "Clube"

    def salary_display(self, obj):
        if obj.salary:
            return format_html(
                '<span title="Restrito">💰 {:.2f} {}</span>',
                obj.salary,
                obj.currency,
            )
        return "—"
    salary_display.short_description = "Salário"

    def signatures_display(self, obj):
        player_ok = "✓" if obj.signed_by_player else "✗"
        club_ok = "✓" if obj.signed_by_club else "✗"
        color = "green" if (obj.signed_by_player and obj.signed_by_club) else "orange"
        return format_html(
            '<span style="color:{};">Jogador {} / Clube {}</span>',
            color, player_ok, club_ok,
        )
    signatures_display.short_description = "Assinaturas"


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "fifa_agent_id", "country", "email", "phone")
    list_filter = ("country", "created_at")
    search_fields = ("name", "email", "fifa_agent_id", "agency")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("👤 Agent", {"fields": ("name", "country")}),
        ("🏢 Agency", {"fields": ("agency", "fifa_agent_id", "license_number")}),
        ("📞 Contact", {"fields": ("email", "phone")}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(PlayerAgentRelationship)
class PlayerAgentRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "player_name", "agent_name", "status",
        "start_date", "end_date", "commission_rate_display",
    )
    list_filter = ("status", "start_date", "created_at")
    search_fields = ("player__first_name", "player__last_name", "agent__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "agent", "representation_agreement")
    date_hierarchy = "start_date"
    fieldsets = (
        ("👥 Relationship", {"fields": ("player", "agent", "status")}),
        ("📅 Duration", {"fields": ("start_date", "end_date")}),
        ("💰 Commission", {"fields": ("commission_rate",)}),
        ("📄 Agreement", {"fields": ("representation_agreement", "notes")}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def agent_name(self, obj):
        return obj.agent.name
    agent_name.short_description = "Agente"

    def commission_rate_display(self, obj):
        if obj.commission_rate:
            return format_html("{}%", obj.commission_rate)
        return "—"
    commission_rate_display.short_description = "Comissão"


@admin.register(PlayerTrainingHistory)
class PlayerTrainingHistoryAdmin(admin.ModelAdmin):
    """
    EPP/Solidarity Contribution tracking.
    Critical for FIFA training compensation and international transfers.
    """

    list_display = (
        "player_name", "academy_name", "club_name",
        "country", "training_category",
        "start_date", "end_date", "verified_display",
    )
    list_filter = ("training_category", "country", "verified", "start_date")
    search_fields = (
        "player__first_name", "player__last_name",
        "academy_name", "club__name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    raw_id_fields = ("player", "club", "verified_by")
    date_hierarchy = "start_date"
    fieldsets = (
        ("👤 Player & Academy", {"fields": ("player", "academy_name", "club")}),
        ("📅 Period", {"fields": ("start_date", "end_date", "country", "training_category")}),
        (
            "✅ Verification",
            {
                "fields": ("verified", "verified_by", "verified_at"),
                "description": "Must be verified for FIFA Solidarity/EPP compliance.",
            },
        ),
        ("📝 Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def club_name(self, obj):
        return obj.club.name if obj.club else "—"
    club_name.short_description = "Clube"

    def verified_display(self, obj):
        if obj.verified:
            return format_html('<span style="color:green;font-weight:bold;">✓ Verificado</span>')
        return format_html('<span style="color:orange;">⚠ Pendente</span>')
    verified_display.short_description = "Verificação"


# ============================================================================
# PHASE 4 ADMIN CLASSES
# ============================================================================

@admin.register(PlayerMedicalProfile)
class PlayerMedicalProfileAdmin(admin.ModelAdmin):
    """
    ⚠️ RESTRICTED ACCESS — Medical data is confidential.
    Only Club Medical Staff and Authorized Personnel should access.
    """

    list_display = (
        "player_name",
        "medical_status_display",
        "blood_type",
        "medical_clearance_display",
        "last_medical_exam",
    )
    list_filter = ("medical_status", "medical_clearance", "blood_type", "created_at")
    search_fields = ("player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player",)
    fieldsets = (
        ("👤 Player", {"fields": ("player",)}),
        (
            "🏥 Medical Status (Restricted)",
            {
                "fields": (
                    "medical_status",
                    "medical_clearance",
                    "injury_status",
                    "fitness_status",
                ),
                "description": "🔒 CONFIDENTIAL: Access restricted to medical staff.",
            },
        ),
        ("🩸 Blood & Exams", {"fields": ("blood_type", "last_medical_exam", "next_medical_exam")}),
        (
            "📝 Medical Notes (Restricted)",
            {
                "fields": ("medical_notes", "allergies", "current_medications", "medical_conditions"),
                "description": "🔒 CONFIDENTIAL.",
                "classes": ("collapse",),
            },
        ),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def medical_status_display(self, obj):
        colors = {
            "fit": "green",
            "injured": "red",
            "recovering": "orange",
            "suspended_medical": "purple",
        }
        color = colors.get(obj.medical_status, "gray")
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color,
            obj.get_medical_status_display(),
        )
    medical_status_display.short_description = "Estado Médico"

    def medical_clearance_display(self, obj):
        if obj.medical_clearance:
            return format_html('<span style="color:green;font-weight:bold;">✓ Apto</span>')
        return format_html('<span style="color:red;">✗ Não Apto</span>')
    medical_clearance_display.short_description = "Aptidão"


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    """
    ⚠️ RESTRICTED ACCESS — All medical documents are confidential.
    """

    list_display = (
        "title",
        "player_name",
        "document_type",
        "issued_at",
        "expires_at",
        "verification_status_display",
        "is_confidential",
    )
    list_filter = (
        "document_type", "verification_status",
        "is_confidential", "issued_at", "created_at",
    )
    search_fields = ("title", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    raw_id_fields = ("player", "file", "verified_by")
    date_hierarchy = "issued_at"
    fieldsets = (
        ("📄 Document", {"fields": ("player", "document_type", "title", "description")}),
        ("📅 Validity", {"fields": ("issued_at", "expires_at")}),
        ("📎 File", {"fields": ("file",)}),
        (
            "✅ Verification (Restricted)",
            {
                "fields": ("verification_status", "verified_by", "verified_at"),
                "description": "🔒 CONFIDENTIAL.",
            },
        ),
        ("🔒 Access Control", {"fields": ("is_confidential",)}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def verification_status_display(self, obj):
        colors = {
            "pending": "orange",
            "verified": "green",
            "rejected": "red",
            "expired": "gray",
        }
        color = colors.get(obj.verification_status, "gray")
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color,
            obj.get_verification_status_display(),
        )
    verification_status_display.short_description = "Verificação"


@admin.register(NationalTeamCallUp)
class NationalTeamCallUpAdmin(admin.ModelAdmin):
    list_display = (
        "player_name", "national_team", "category",
        "call_up_date", "release_date", "status", "caps",
    )
    list_filter = ("national_team", "category", "status", "call_up_date")
    search_fields = ("player__first_name", "player__last_name", "national_team")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "competition")
    date_hierarchy = "call_up_date"
    fieldsets = (
        ("👤 Player & Team", {"fields": ("player", "national_team", "category")}),
        ("📅 Call-up", {"fields": ("call_up_date", "release_date", "status")}),
        ("⚽ Competition & Caps", {"fields": ("competition", "caps", "goals", "assists")}),
        ("📝 Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"


@admin.register(PlayerPerformanceMetric)
class PlayerPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = (
        "player_name", "metric_type", "value_display", "recorded_at", "source",
    )
    list_filter = ("metric_type", "source", "recorded_at")
    search_fields = ("player__first_name", "player__last_name", "metric_type")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "match")
    date_hierarchy = "recorded_at"
    fieldsets = (
        ("📊 Metric", {"fields": ("player", "match", "metric_type", "value", "unit")}),
        ("📅 Recording", {"fields": ("recorded_at", "source")}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def value_display(self, obj):
        return format_html("{} {}", obj.value, obj.unit)
    value_display.short_description = "Valor"


@admin.register(PlayerComplianceRecord)
class PlayerComplianceRecordAdmin(admin.ModelAdmin):
    """
    FIFA RSTP compliance tracking.
    Covers: minor transfers, work permits, international transfer rules.
    """

    list_display = (
        "player_name", "rule_type_display",
        "status_display", "priority_display", "reviewed_at",
    )
    list_filter = ("rule_type", "status", "priority", "reviewed_at")
    search_fields = ("player__first_name", "player__last_name", "rule_type")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "reviewed_by")
    date_hierarchy = "reviewed_at"
    fieldsets = (
        ("👤 Player & Rule", {"fields": ("player", "rule_type", "priority")}),
        ("✅ Status", {"fields": ("status", "notes")}),
        ("🔍 Review", {"fields": ("reviewed_by", "reviewed_at")}),
        ("📊 Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def player_name(self, obj):
        return obj.player.full_name
    player_name.short_description = "Jogador"

    def rule_type_display(self, obj):
        return obj.get_rule_type_display()
    rule_type_display.short_description = "Regra"

    def status_display(self, obj):
        colors = {
            "compliant": "green",
            "non_compliant": "red",
            "pending_review": "orange",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_display.short_description = "Estado"

    def priority_display(self, obj):
        colors = {
            "critical": "red",
            "high": "orange",
            "medium": "blue",
            "low": "gray",
        }
        color = colors.get(obj.priority, "gray")
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color,
            obj.get_priority_display(),
        )
    priority_display.short_description = "Prioridade"
