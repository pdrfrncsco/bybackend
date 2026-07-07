# BOLAYETU_CLOUDFLARE_SKILL.md

Bolayetu uses Cloudflare as its primary edge infrastructure.

Every new feature must consider Cloudflare integration.

Infrastructure:

* Cloudflare CDN
* Cloudflare R2
* Cloudflare DNS
* Cloudflare SSL
* Cloudflare Cache
* Cloudflare WAF
* Cloudflare Turnstile
* Cloudflare Zero Trust (future)

---

# MEDIA STORAGE

Never store media files inside Django.

Forbidden:

MEDIA_ROOT
MEDIA_URL
Local file storage

Use:

Cloudflare R2

Storage backend:

django-storages
boto3

All uploaded files must be stored in R2.

Examples:

Player Photos

Club Logos

Club Banners

Player Videos

Competition Documents

Reports

PDF Files

---

# FILE URLS

Always return public CDN URLs.

Example:

https://cdn.bolayetu.com/players/photo.jpg

Never expose local filesystem paths.

Forbidden:

/media/player.jpg

---

# STATIC FILES

Use:

WhiteNoise

or

Cloudflare CDN

Frontend assets should be cached aggressively.

---

# CACHE STRATEGY

Use Cloudflare Cache whenever possible.

Recommended:

Images:
1 year

Videos:
1 year

Static Assets:
1 year

API:
Short TTL

Never cache authenticated API responses.

---

# IMAGE OPTIMIZATION

Prepare frontend and backend for:

* WebP
* AVIF
* Lazy Loading
* Responsive Images

---

# SECURITY

Use Cloudflare WAF.

Protect:

Authentication endpoints

Admin endpoints

API endpoints

Uploads

---

# DNS

All tenant subdomains must be managed through Cloudflare.

Examples:

faf.bolayetu.com

girabola.bolayetu.com

petro.bolayetu.com

Always design new features assuming Cloudflare DNS management.
