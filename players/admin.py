"""
BOLAYETU — Players Admin

Comprehensive admin interface for Players module with Phases 3-4 implementations:
- Phase 1-2: Player, Registration, Documents, Videos, Achievements
- Phase 3: Contracts, Agents, Training History
- Phase 4: Medical Data, National Team, Performance, Compliance

Privacy Note: Medical data access is restricted via is_confidential field.
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
# PHASE 3 INLINES — Professional (Contracts, Agents, Training)
# ============================================================================


class PlayerContractInline(admin.TabularInline):
    """Inline for contracts within Player admin."""

    model = PlayerContract
    extra = 0
    raw_id_fields = ("club", "contract_document", "verified_by")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fields = (
        "contract_type",
        "club",
        "status",
        "start_date",
        "end_date",
        "salary",
        "signed_by_player",
        "signed_by_club",
        "created_at",
    )


class PlayerAgentRelationshipInline(admin.TabularInline):
    """Inline for agent relationships within Player admin."""

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
        "created_at",
    )


class PlayerTrainingHistoryInline(admin.TabularInline):
    """Inline for training history within Player admin."""

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
        "created_at",
    )


# ============================================================================
# PHASE 4 INLINES — Medical, National Team, Performance, Compliance
# ============================================================================


class MedicalDocumentInline(admin.TabularInline):
    """Inline for medical documents within Player admin (Phase 4)."""

    model = MedicalDocument
    extra = 0
    raw_id_fields = ("file", "verified_by")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "verified_at",
        "is_valid_status",
        "is_confidential_status",
    )
    fields = (
        "document_type",
        "title",
        "issued_at",
        "expires_at",
        "verification_status",
        "is_valid_status",
        "is_confidential_status",
        "created_at",
    )

    def is_valid_status(self, obj):
        """Display validity status."""
        if obj.is_valid:
            return format_html(
                '<span style="color: green;">✓ Válido</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inválido</span>'
        )

    is_valid_status.short_description = "Validade"

    def is_confidential_status(self, obj):
        """Display confidentiality status."""
        if obj.is_confidential:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔒 Confidencial</span>'
            )
        return format_html(
            '<span style="color: orange;">⚠ Não Confidencial</span>'
        )

    is_confidential_status.short_description = "Confidencialidade"


class NationalTeamCallUpInline(admin.TabularInline):
    """Inline for national team call-ups within Player admin."""

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
        "created_at",
    )


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """
    Main Player admin interface with comprehensive sections for all phases.
    Includes identity, contact, football, career, contracts, medical, and compliance info.
    """

    list_display = (
        "full_name",
        "global_id_display",
        "primary_position",
        "status",
        "nationality",
        "user",
        "contract_status_display",
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
        "is_minor",
    )
    raw_id_fields = ("user", "profile_photo")

    # All inlines for complete player profile
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
                    "is_minor",
                    "nationality",
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
                "description": "⚠️ DEPRECATED: Use PlayerContact and EmergencyContact models. Migrate to /api/v1/players/{id}/contact/ endpoint.",
                "classes": ("collapse",),
            },
        ),
        (
            "⚽ Football Profile",
            {
                "fields": (
                    "primary_position",
                    "foot",
                    "height_cm",
                    "weight_kg",
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
                "description": "Use 'profile_photo' (media asset) for new uploads. 'avatar' is deprecated.",
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
        """Display global_id with formatting."""
        if obj.global_id:
            return format_html(
                '<code style="background-color: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{}</code>',
                obj.global_id,
            )
        return "—"

    global_id_display.short_description = "Global ID"

    def contract_status_display(self, obj):
        """Display active contract status."""
        active_contract = obj.contracts.filter(status="active").first()
        if active_contract:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                active_contract.club.name,
            )
        return mark_safe('<span style="color: gray;">—</span>')

    contract_status_display.short_description = "Contrato Atual"


@admin.register(PlayerRegistration)
class PlayerRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "club",
        "competition",
        "tenant",
        "shirt_number",
        "joined_date",
        "left_date",
        "status",
    )
    list_filter = ("status", "tenant", "joined_date")
    search_fields = (
        "player__first_name",
        "player__last_name",
        "club__name",
        "competition__name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "club", "competition", "tenant")
    date_hierarchy = "joined_date"
    fieldsets = (
        (
            "Registration",
            {
                "fields": (
                    "player",
                    "club",
                    "competition",
                    "tenant",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "shirt_number",
                    "joined_date",
                    "left_date",
                    "status",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "matches_played",
                    "goals",
                    "assists",
                    "yellow_cards",
                    "red_cards",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(PlayerRegistrationRequest)
class PlayerRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("player", "club", "status", "joined_date", "submitted_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("player__first_name", "player__last_name", "club__name")
    readonly_fields = ("id", "created_at", "updated_at", "reviewed_at")
    raw_id_fields = ("player", "club", "tenant", "competition", "submitted_by", "reviewed_by", "registration")


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
# PHASE 3 ADMIN CLASSES — Professional (Contracts, Agents, Training)
# ============================================================================


@admin.register(PlayerContract)
class PlayerContractAdmin(admin.ModelAdmin):
    """
    Admin for PlayerContract with financial and legal details.
    
    Restricted Access: Contract visibility controlled by PlayerPrivacySettings.
    Only club staff and authorized personnel should view salary/financial terms.
    """

    list_display = (
        "player_name",
        "club_name",
        "contract_type",
        "status",
        "start_date",
        "end_date",
        "salary_display",
        "is_active_status",
        "is_fully_signed_status",
    )
    list_filter = (
        "status",
        "contract_type",
        "start_date",
        "created_at",
        "signed_by_player",
        "signed_by_club",
    )
    search_fields = (
        "player__first_name",
        "player__last_name",
        "club__name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "verified_at",
        "is_active",
        "is_fully_signed",
    )
    raw_id_fields = (
        "player",
        "club",
        "tenant",
        "contract_document",
        "verified_by",
    )
    date_hierarchy = "start_date"

    fieldsets = (
        (
            "📋 Basic Information",
            {
                "fields": (
                    "player",
                    "club",
                    "contract_type",
                    "status",
                )
            },
        ),
        (
            "📅 Contract Period",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "signed_date",
                )
            },
        ),
        (
            "💰 Financial Terms (Restricted)",
            {
                "fields": (
                    "salary",
                    "currency",
                    "bonuses",
                    "release_clause",
                ),
                "description": "⚠️ RESTRICTED: Salary and financial terms visible only to authorized personnel.",
            },
        ),
        (
            "📜 Contract Clauses",
            {
                "fields": (
                    "has_image_rights",
                    "option_year",
                    "termination_clause",
                )
            },
        ),
        (
            "✍️ Signatures & Verification",
            {
                "fields": (
                    "signed_by_player",
                    "signed_by_club",
                    "is_fully_signed",
                    "verified_by",
                    "verified_at",
                    "is_active",
                )
            },
        ),
        (
            "📄 Documentation",
            {
                "fields": ("contract_document",)
            },
        ),
        (
            "🏢 Organization",
            {
                "fields": ("tenant",),
                "classes": ("collapse",),
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def club_name(self, obj):
        return obj.club.name

    club_name.short_description = "Clube"

    def salary_display(self, obj):
        """Display salary with currency and privacy warning."""
        if obj.salary:
            return format_html(
                '<span title="Restrito">💰 {:.2f} {}</span>',
                obj.salary,
                obj.currency,
            )
        return "—"

    salary_display.short_description = "Salário"

    def is_active_status(self, obj):
        """Display active status."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Ativo</span>'
            )
        return format_html('<span style="color: gray;">✗ Inativo</span>')

    is_active_status.short_description = "Estado"

    def is_fully_signed_status(self, obj):
        """Display signing status."""
        if obj.is_fully_signed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Assinado</span>'
            )
        parts = []
        if not obj.signed_by_player:
            parts.append("Jogador")
        if not obj.signed_by_club:
            parts.append("Clube")
        return format_html(
            '<span style="color: orange;">⚠ Aguarda: {}</span>',
            ", ".join(parts),
        )

    is_fully_signed_status.short_description = "Assinatura"


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin for Agent entity (represents a player agent/representative)."""

    list_display = (
        "name",
        "fifa_agent_id",
        "country",
        "email",
        "phone",
    )
    list_filter = ("country", "created_at")
    search_fields = ("name", "email", "fifa_agent_id", "agency")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (
            "👤 Personal Information",
            {
                "fields": (
                    "name",
                    "country",
                )
            },
        ),
        (
            "🏢 Agency Details",
            {
                "fields": (
                    "agency",
                    "fifa_agent_id",
                    "license_number",
                )
            },
        ),
        (
            "📞 Contact",
            {
                "fields": (
                    "email",
                    "phone",
                )
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PlayerAgentRelationship)
class PlayerAgentRelationshipAdmin(admin.ModelAdmin):
    """Admin for Player-Agent relationships."""

    list_display = (
        "player_name",
        "agent_name",
        "status",
        "start_date",
        "end_date",
        "commission_rate_display",
    )
    list_filter = ("status", "start_date", "created_at")
    search_fields = (
        "player__first_name",
        "player__last_name",
        "agent__name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "agent", "representation_agreement")
    date_hierarchy = "start_date"

    fieldsets = (
        (
            "👥 Relationship",
            {
                "fields": (
                    "player",
                    "agent",
                    "status",
                )
            },
        ),
        (
            "📅 Duration",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "💰 Commission",
            {
                "fields": ("commission_rate",),
                "description": "Commission percentage charged by the agent.",
            },
        ),
        (
            "📄 Documentation",
            {
                "fields": ("representation_agreement",)
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def agent_name(self, obj):
        return obj.agent.name

    agent_name.short_description = "Agente"

    def commission_rate_display(self, obj):
        """Display commission rate."""
        if obj.commission_rate:
            return format_html("{}%", obj.commission_rate)
        return "—"

    commission_rate_display.short_description = "Comissão"


@admin.register(PlayerTrainingHistory)
class PlayerTrainingHistoryAdmin(admin.ModelAdmin):
    """
    Admin for PlayerTrainingHistory (EPP/Solidarity Contribution record).
    
    Critical for: Training compensation calculations, Solidarity contribution tracking,
    International transfer compliance (FIFA RSTP).
    """

    list_display = (
        "player_name",
        "academy_name",
        "club_name",
        "country",
        "training_category",
        "start_date",
        "end_date",
        "verified_status",
    )
    list_filter = (
        "training_category",
        "country",
        "verified",
        "start_date",
        "created_at",
    )
    search_fields = (
        "player__first_name",
        "player__last_name",
        "academy_name",
        "club__name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "verified_at",
    )
    raw_id_fields = ("player", "club", "verified_by")
    date_hierarchy = "start_date"

    fieldsets = (
        (
            "👤 Player & Academy",
            {
                "fields": (
                    "player",
                    "academy_name",
                    "club",
                )
            },
        ),
        (
            "📅 Training Period",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "country",
                    "training_category",
                )
            },
        ),
        (
            "✅ Verification",
            {
                "fields": (
                    "verified",
                    "verified_by",
                    "verified_at",
                ),
                "description": "Training history must be verified for FIFA compliance (EPP/Solidarity calculations).",
            },
        ),
        (
            "📝 Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def club_name(self, obj):
        return obj.club.name if obj.club else "—"

    club_name.short_description = "Clube"

    def verified_status(self, obj):
        """Display verification status."""
        if obj.verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verificado</span>'
            )
        return format_html('<span style="color: orange;">⚠ Pendente</span>')

    verified_status.short_description = "Verificação"


# ============================================================================
# PHASE 4 ADMIN CLASSES — Medical, National Team, Performance, Compliance
# ============================================================================


@admin.register(PlayerMedicalProfile)
class PlayerMedicalProfileAdmin(admin.ModelAdmin):
    """
    Admin for PlayerMedicalProfile.
    
    ⚠️ RESTRICTED ACCESS: Medical data is confidential.
    Only Club Medical Staff and Authorized Personnel should access.
    """

    list_display = (
        "player_name",
        "medical_status_display",
        "blood_type",
        "medical_clearance_display",
        "last_medical_exam",
        "needs_exam_display",
    )
    list_filter = (
        "medical_status",
        "medical_clearance",
        "blood_type",
        "last_medical_exam",
        "created_at",
    )
    search_fields = ("player__first_name", "player__last_name")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "is_fit_to_play",
        "needs_medical_exam",
    )
    raw_id_fields = ("player",)

    fieldsets = (
        (
            "👤 Player",
            {
                "fields": ("player",)
            },
        ),
        (
            "🏥 Medical Status (Restricted)",
            {
                "fields": (
                    "medical_status",
                    "medical_clearance",
                    "is_fit_to_play",
                    "injury_status",
                ),
                "description": "🔒 CONFIDENTIAL: Medical status information.",
            },
        ),
        (
            "🩸 Blood & Physical",
            {
                "fields": (
                    "blood_type",
                    "fitness_status",
                )
            },
        ),
        (
            "📅 Medical Examinations",
            {
                "fields": (
                    "last_medical_exam",
                    "next_medical_exam",
                    "needs_medical_exam",
                ),
                "description": "Track medical examination schedule.",
            },
        ),
        (
            "📝 Medical Notes (Restricted)",
            {
                "fields": (
                    "medical_notes",
                    "allergies",
                    "current_medications",
                    "medical_conditions",
                ),
                "description": "🔒 CONFIDENTIAL: Detailed medical information.",
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def medical_status_display(self, obj):
        """Display medical status with color coding."""
        status_colors = {
            "fit": "green",
            "injured": "red",
            "recovering": "orange",
            "suspended_medical": "purple",
        }
        color = status_colors.get(obj.medical_status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_medical_status_display(),
        )

    medical_status_display.short_description = "Estado Médico"

    def medical_clearance_display(self, obj):
        """Display medical clearance status."""
        if obj.medical_clearance:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Apto</span>'
            )
        return format_html('<span style="color: red;">✗ Não Apto</span>')

    medical_clearance_display.short_description = "Aptidão"

    def needs_exam_display(self, obj):
        """Display if medical exam is needed."""
        if obj.needs_medical_exam:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Sim</span>'
            )
        return format_html('<span style="color: green;">✓ Não</span>')

    needs_exam_display.short_description = "Exame Devido"


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    """
    Admin for MedicalDocument.
    
    ⚠️ RESTRICTED ACCESS: All medical documents are confidential.
    Only medical staff and authorized personnel should access.
    """

    list_display = (
        "title",
        "player_name",
        "document_type",
        "issued_at",
        "expires_at",
        "verification_status_display",
        "is_valid_display",
        "is_confidential_display",
    )
    list_filter = (
        "document_type",
        "verification_status",
        "is_confidential",
        "issued_at",
        "expires_at",
        "created_at",
    )
    search_fields = (
        "title",
        "player__first_name",
        "player__last_name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "verified_at",
        "is_valid",
        "is_expired",
    )
    raw_id_fields = ("player", "file", "verified_by")
    date_hierarchy = "issued_at"

    fieldsets = (
        (
            "📄 Document Details",
            {
                "fields": (
                    "player",
                    "document_type",
                    "title",
                    "description",
                )
            },
        ),
        (
            "📅 Validity Period",
            {
                "fields": (
                    "issued_at",
                    "expires_at",
                    "is_expired",
                )
            },
        ),
        (
            "📎 File",
            {
                "fields": ("file",)
            },
        ),
        (
            "✅ Verification (Restricted)",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "is_valid",
                ),
                "description": "🔒 CONFIDENTIAL: Document verification status.",
            },
        ),
        (
            "🔒 Access Control",
            {
                "fields": ("is_confidential",),
                "description": "If checked, only medical staff can access this document.",
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def verification_status_display(self, obj):
        """Display verification status with color."""
        status_colors = {
            "pending": "orange",
            "verified": "green",
            "rejected": "red",
            "expired": "gray",
        }
        color = status_colors.get(obj.verification_status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_verification_status_display(),
        )

    verification_status_display.short_description = "Verificação"

    def is_valid_display(self, obj):
        """Display validity status."""
        if obj.is_valid:
            return format_html(
                '<span style="color: green;">✓ Válido</span>'
            )
        return format_html('<span style="color: red;">✗ Inválido</span>')

    is_valid_display.short_description = "Validade"

    def is_confidential_display(self, obj):
        """Display confidentiality status."""
        if obj.is_confidential:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔒 Confidencial</span>'
            )
        return format_html(
            '<span style="color: orange;">⚠ Não Confidencial</span>'
        )

    is_confidential_display.short_description = "Confidencialidade"


@admin.register(NationalTeamCallUp)
class NationalTeamCallUpAdmin(admin.ModelAdmin):
    """Admin for National Team Call-ups."""

    list_display = (
        "player_name",
        "national_team",
        "category",
        "call_up_date",
        "release_date",
        "status",
        "caps",
    )
    list_filter = (
        "national_team",
        "category",
        "status",
        "call_up_date",
        "created_at",
    )
    search_fields = (
        "player__first_name",
        "player__last_name",
        "national_team",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "competition")
    date_hierarchy = "call_up_date"

    fieldsets = (
        (
            "👤 Player & National Team",
            {
                "fields": (
                    "player",
                    "national_team",
                    "category",
                )
            },
        ),
        (
            "📅 Call-up Period",
            {
                "fields": (
                    "call_up_date",
                    "release_date",
                    "status",
                )
            },
        ),
        (
            "⚽ Competition & Caps",
            {
                "fields": (
                    "competition",
                    "caps",
                )
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"


@admin.register(PlayerPerformanceMetric)
class PlayerPerformanceMetricAdmin(admin.ModelAdmin):
    """Admin for Player Performance Metrics (GPS/Biometric data)."""

    list_display = (
        "player_name",
        "metric_type",
        "value_display",
        "recorded_at",
        "source",
    )
    list_filter = (
        "metric_type",
        "source",
        "recorded_at",
    )
    search_fields = (
        "player__first_name",
        "player__last_name",
        "metric_type",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "match")
    date_hierarchy = "recorded_at"

    fieldsets = (
        (
            "📊 Performance Data",
            {
                "fields": (
                    "player",
                    "match",
                    "metric_type",
                    "value",
                    "unit",
                )
            },
        ),
        (
            "📅 Recording",
            {
                "fields": (
                    "recorded_at",
                    "source",
                )
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def value_display(self, obj):
        """Display performance value with unit."""
        return format_html("{} {}", obj.value, obj.unit)

    value_display.short_description = "Valor"


@admin.register(PlayerComplianceRecord)
class PlayerComplianceRecordAdmin(admin.ModelAdmin):
    """
    Admin for PlayerComplianceRecord (FIFA RSTP, Work Permit, Transfer Compliance).
    
    Tracks: Minor transfer compliance, Work permit status, Contract compliance,
    International transfer rules, Eligibility requirements.
    """

    list_display = (
        "player_name",
        "rule_type",
        "status_display",
        "priority_display",
        "reviewed_at",
    )
    list_filter = (
        "rule_type",
        "status",
        "priority",
        "reviewed_at",
        "created_at",
    )
    search_fields = (
        "player__first_name",
        "player__last_name",
        "rule_type",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "reviewed_by")
    date_hierarchy = "reviewed_at"

    fieldsets = (
        (
            "👤 Player & Rule",
            {
                "fields": (
                    "player",
                    "rule_type",
                    "priority",
                )
            },
        ),
        (
            "✅ Compliance Status",
            {
                "fields": (
                    "status",
                    "notes",
                )
            },
        ),
        (
            "🔍 Review",
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                ),
                "description": "Track compliance reviews and approvals.",
            },
        ),
        (
            "📊 Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def player_name(self, obj):
        return obj.player.full_name

    player_name.short_description = "Jogador"

    def status_display(self, obj):
        """Display compliance status with color."""
        status_colors = {
            "compliant": "green",
            "non_compliant": "red",
            "pending_review": "orange",
        }
        color = status_colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Estado"

    def priority_display(self, obj):
        """Display priority level."""
        priority_colors = {
            "critical": "red",
            "high": "orange",
            "medium": "blue",
            "low": "gray",
        }
        color = priority_colors.get(obj.priority, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    priority_display.short_description = "Prioridade"
