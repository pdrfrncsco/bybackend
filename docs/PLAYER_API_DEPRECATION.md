# Player API Deprecation Notice

## Compatibility Window: 2 Sprints (August - September 2026)

This document outlines the deprecation of Player model fields and the migration path to new models.

---

## Deprecated Fields

### 1. **Player.email** → **PlayerContact.primary_email**
- **Status**: Deprecated (will be removed after 2-sprint compatibility window)
- **Reason**: Centralizes contact management in PlayerContact model
- **Migration Path**: 
  - Use `GET /api/v1/players/{player_id}/contacts/` to fetch primary_email
  - Use `PATCH /api/v1/players/{player_id}/contacts/` to update email
  - Backend already backfills PlayerContact from player.email on player creation

### 2. **Player.phone** → **PlayerContact.mobile_phone**
- **Status**: Deprecated (will be removed after 2-sprint compatibility window)
- **Reason**: Centralizes contact management in PlayerContact model
- **Migration Path**:
  - Use `GET /api/v1/players/{player_id}/contacts/` to fetch mobile_phone
  - Use `PATCH /api/v1/players/{player_id}/contacts/` to update phone
  - Backend already backfills PlayerContact from player.phone on player creation

### 3. **Player.avatar** (URL field) → **Player.profile_photo** (MediaAsset FK)
- **Status**: Deprecated (will be removed after 2-sprint compatibility window)
- **Reason**: Integration with media asset system (DAM) enables better asset management
- **Migration Path**:
  - New avatars uploaded via `POST /api/v1/players/{player_id}/avatar/` now set **both**:
    - `profile_photo` FK to MediaAsset (preferred)
    - `avatar` URL field (backwards compatibility)
  - Use `profile_photo_url` property (readonly) to get the current photo URL:
    - Returns `profile_photo.public_url` if profile_photo exists
    - Falls back to `avatar` URL if no profile_photo
  - After compatibility window, clients must reference `profile_photo_url` only

---

## API Contract Changes

### PlayerSerializer & PlayerDetailSerializer

All Player endpoints return deprecated fields for backwards compatibility:

```json
{
  "id": "uuid",
  "slug": "player-slug",
  "first_name": "João",
  "last_name": "Silva",
  "email": "joao@example.com",          // ⚠️ DEPRECATED → Use PlayerContact.primary_email
  "phone": "+351912345678",              // ⚠️ DEPRECATED → Use PlayerContact.mobile_phone
  "avatar": "https://assets.../avatar.jpg",  // ⚠️ DEPRECATED → Use profile_photo_url
  "profile_photo_url": "https://assets.../photo.jpg",  // ✅ NEW: Use this
  "profile_photo": null,  // Internal FK, not exposed in serializer (reference: players/serializers/__init__.py)
  "created_at": "2026-08-08T...",
  "updated_at": "2026-08-10T..."
}
```

### New Endpoints (PlayerContact)

```bash
# Get player's contact info (including deprecated fallbacks)
GET /api/v1/players/{player_id}/contacts/

# Update player's contact info
PATCH /api/v1/players/{player_id}/contacts/
{
  "primary_email": "new.email@example.com",
  "mobile_phone": "+351912345679"
}
```

Response:
```json
{
  "id": "uuid",
  "player_id": "uuid",
  "primary_email": "new.email@example.com",
  "mobile_phone": "+351912345679",
  "secondary_emails": [],
  "additional_phones": [],
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Migration Checklist

### Backend Tasks (Completed)
- ✅ Created PlayerContact model with primary_email, mobile_phone fields
- ✅ Added profile_photo FK to Player (references media_assets.MediaAsset)
- ✅ Added contact_email/contact_phone properties to Player (with fallback logic)
- ✅ Added profile_photo_url property to Player (prefers asset URL, falls back to avatar)
- ✅ Updated PlayerService.create_player to backfill PlayerContact
- ✅ Updated PlayerService.upload_avatar to set both profile_photo FK and avatar URL
- ✅ Created API endpoints for PlayerContact CRUD
- ✅ Updated serializers with deprecation notice in docstrings
- ✅ Updated admin.py to group deprecated fields with warnings

### Client Tasks (Required within 2 sprints)
- [ ] Mobile/Web clients stop sending/reading email, phone, avatar from /api/v1/players/ responses
- [ ] Mobile/Web clients updated to use /api/v1/players/{id}/contacts/ for contact info
- [ ] Analytics/dashboards updated to reference profile_photo_url instead of avatar
- [ ] External scripts updated to use new contact endpoints if applicable

### Post-Compatibility Window Tasks (End of September 2026)
- [ ] Create migration: `DROP COLUMN player.email, player.phone, player.avatar`
- [ ] Update codebase to remove fallback properties and deprecated field references
- [ ] Update test fixtures that reference deprecated fields
- [ ] Run full test suite + staging DB migration test
- [ ] Release with deprecation removal announced in release notes

---

## Backfill Strategy

### Existing Players (No Action Required)
- `PlayerContact` is auto-created when PlayerService.create_player is called
- Existing players' email/phone are accessible via both:
  - Old: `player.email`, `player.phone`
  - New: `player.contact.primary_email`, `player.contact.mobile_phone`

### Avatar Migration (Optional)
- If player has a DAM media asset, consider auto-linking it as profile_photo
- Script to run (after compatibility window, before column drop):
  ```python
  # Bulk link existing media assets to players if no profile_photo set
  for player in Player.objects.filter(profile_photo__isnull=True, avatar__isnull=False):
      # Query media_assets for this player's avatar
      assets = MediaAsset.objects.filter(
          owner_type='player', owner_id=player.id, role='avatar'
      ).order_by('-created_at')
      if assets.exists():
          player.profile_photo = assets.first()
          player.save(update_fields=['profile_photo'])
  ```

---

## FAQ

### Q: When will deprecated fields be removed?
**A**: End of September 2026 (2-sprint compatibility window), pending client migration completion.

### Q: What if my client still sends player.email in POST/PATCH?
**A**: Still accepted and stored in Player.email + backfilled to PlayerContact.primary_email (no breaking changes during compatibility window).

### Q: Should I migrate now or wait?
**A**: Migrate on your timeline within the 2-sprint window. The backend will support both old and new patterns until the column drop.

### Q: What about external consumers (analytics, third-party apps)?
**A**: External APIs and dashboards must be notified. A separate communication will be sent to external integrators.

---

## References
- [PLAYER_MODULE_ROADMAP.md](./PLAYER_MODULE_ROADMAP.md) — Phase 1 (Identity) design
- [players/models/contact.py](../players/models/contact.py) — PlayerContact model
- [players/serializers/player_contact.py](../players/serializers/player_contact.py) — ContactSerializer
- [players/views/player_contact_views.py](../players/views/player_contact_views.py) — Contact endpoints
- [01_CODING_STANDARDS.md](./01_CODING_STANDARDS.md) — Backend architecture patterns
