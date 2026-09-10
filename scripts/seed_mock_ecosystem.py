"""
BOLAYETU — Seed Mock Ecosystem Generator

Gera um ecossistema completo de dados mock no Bolayetu:
  1. Organizações (Tenants): Federações, Associações e Ligas provinciais
  2. Clubes: Clubes angolanos autênticos com estádio, cidade e equipa técnica
  3. Jogadores: Atletas globais com atributos físicos, fotos/avatares e registos no plantel (PlayerRegistration)
  4. Competições: Ligas e Taças com inscrições de clubes, tabela de classificação (Standings) e jogos (Matches)
  5. Vínculo de Utilizador: Associa opcionalmente um utilizador administrador/gestor ao clube principal

Uso no PowerShell / Terminal:
    cd bybackend
    python scripts/seed_mock_ecosystem.py
    python scripts/seed_mock_ecosystem.py --user-email="admin@bolayetu.com"
    python scripts/seed_mock_ecosystem.py --clubs-per-org=8 --players-per-club=25
    python scripts/seed_mock_ecosystem.py --clean
    python scripts/seed_mock_ecosystem.py --dry-run

Também pode ser executado como comando Django:
    python manage.py seed_mock_ecosystem
"""

import os
import sys
import random
import datetime
import argparse
import urllib.parse
from typing import Optional, List, Dict, Tuple

# ── Django Bootstrap ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

# ── Model Imports ────────────────────────────────────────────────────────────
from core.models import Tenant
from accounts.models import User, TenantMembership
from accounts.constants import MembershipRole
from clubs.models import Club, ClubMember
from clubs.constants import ClubMemberRole
from players.models import Player, PlayerRegistration
from competitions.models import (
    Competition,
    CompetitionRegistration,
    Standing,
    Match,
)
from competitions.constants import CompetitionType, CompetitionStatus


# ── Mock Data Catalog ────────────────────────────────────────────────────────

ORGANIZATIONS_DATA = [
    {
        "name": "Federação Angolana de Futebol",
        "slug": "faf",
        "type": Tenant.TenantType.FEDERATION,
        "subdomain": "faf",
        "primary_color": "#C8102E",
        "secondary_color": "#FFCD00",
        "city": "Luanda",
        "country": "Angola",
        "email": "contacto@faf.co.ao",
        "phone": "+244 923 000 100",
        "website": "https://faf.co.ao",
        "description": "Órgão máximo que tutela a prática do futebol em todo o território nacional de Angola.",
    },
    {
        "name": "Associação Provincial de Futebol de Luanda",
        "slug": "apfl",
        "type": Tenant.TenantType.ASSOCIATION,
        "subdomain": "apfl",
        "primary_color": "#014D40",
        "secondary_color": "#94D3C1",
        "city": "Luanda",
        "country": "Angola",
        "email": "geral@apfl.ao",
        "phone": "+244 923 000 200",
        "website": "https://apfl.ao",
        "description": "Responsável pela organização e desenvolvimento das competições associativas em Luanda.",
    },
    {
        "name": "Liga Nacional de Futebol Profissional",
        "slug": "lnfp",
        "type": Tenant.TenantType.LEAGUE,
        "subdomain": "lnfp",
        "primary_color": "#1E3A8A",
        "secondary_color": "#60A5FA",
        "city": "Luanda",
        "country": "Angola",
        "email": "info@lnfp.ao",
        "phone": "+244 923 000 300",
        "website": "https://lnfp.ao",
        "description": "Entidade organizadora das divisões profissionais de futebol em Angola.",
    },
]

CLUBS_DATA = [
    {
        "name": "Petro Atlético de Luanda",
        "slug": "petro-de-luanda",
        "short_name": "PLU",
        "founded_year": 1980,
        "stadium_name": "Estádio 11 de Novembro",
        "stadium_capacity": 48000,
        "city": "Luanda",
        "country": "Angola",
        "primary_color": "#FFD100",
        "secondary_color": "#003893",
        "email": "geral@petroatletico.co.ao",
        "phone": "+244 923 111 001",
        "website": "https://petroatletico.co.ao",
        "description": "O Clube Atlético Petróleos de Luanda é um dos maiores e mais titulados clubes de futebol de Angola.",
    },
    {
        "name": "Clube Desportivo 1º de Agosto",
        "slug": "primeiro-de-agosto",
        "short_name": "PRI",
        "founded_year": 1977,
        "stadium_name": "Estádio França Ndalu",
        "stadium_capacity": 20000,
        "city": "Luanda",
        "country": "Angola",
        "primary_color": "#D90429",
        "secondary_color": "#000000",
        "email": "secretaria@1deagosto.com",
        "phone": "+244 923 111 002",
        "website": "https://1deagosto.com",
        "description": "Clube Desportivo 1º de Agosto, fundado em 1977 pelas Forças Armadas Angolanas, clube histórico multicampeão.",
    },
    {
        "name": "Grupo Desportivo Sagrada Esperança",
        "slug": "sagrada-esperanca",
        "short_name": "SAG",
        "founded_year": 1976,
        "stadium_name": "Estádio Sagrada Esperança",
        "stadium_capacity": 8000,
        "city": "Dundo",
        "country": "Angola",
        "primary_color": "#16A34A",
        "secondary_color": "#FFFFFF",
        "email": "contacto@sagradaesperanca.ao",
        "phone": "+244 923 111 003",
        "website": "https://sagradaesperanca.ao",
        "description": "Clube da Lunda Norte patrocinado pela Endiama, com presença regular nas provas continentais africanas.",
    },
    {
        "name": "Interclube de Luanda",
        "slug": "interclube",
        "short_name": "INT",
        "founded_year": 1976,
        "stadium_name": "Estádio 22 de Junho",
        "stadium_capacity": 12000,
        "city": "Luanda",
        "country": "Angola",
        "primary_color": "#2563EB",
        "secondary_color": "#FFFFFF",
        "email": "info@interclube.ao",
        "phone": "+244 923 111 004",
        "website": "https://interclube.ao",
        "description": "Grupo Desportivo Interclube, fundado pelo Ministério do Interior da República de Angola.",
    },
    {
        "name": "Wiliete Sport Clube de Benguela",
        "slug": "wiliete-sc",
        "short_name": "WIL",
        "founded_year": 2018,
        "stadium_name": "Estádio de Ombaka",
        "stadium_capacity": 35000,
        "city": "Benguela",
        "country": "Angola",
        "primary_color": "#0284C7",
        "secondary_color": "#F0F9FF",
        "email": "geral@wilietesc.ao",
        "phone": "+244 923 111 005",
        "website": "https://wilietesc.ao",
        "description": "Clube emergente e vibrante da província de Benguela com forte aposta na formação de jovens.",
    },
    {
        "name": "Académica Petróleos do Lobito",
        "slug": "academica-lobito",
        "short_name": "ACA",
        "founded_year": 1970,
        "stadium_name": "Estádio do Buraco",
        "stadium_capacity": 15000,
        "city": "Lobito",
        "country": "Angola",
        "primary_color": "#111827",
        "secondary_color": "#FFFFFF",
        "email": "contacto@academicadoburaco.ao",
        "phone": "+244 923 111 006",
        "website": "https://academicadoburaco.ao",
        "description": "Clube tradicional da cidade do Lobito, conhecido pelos fervorosos adeptos e mística caseira.",
    },
    {
        "name": "Clube Desportivo da Huíla",
        "slug": "desportivo-da-huila",
        "short_name": "CDH",
        "founded_year": 1998,
        "stadium_name": "Estádio da Tundavala",
        "stadium_capacity": 20000,
        "city": "Lubango",
        "country": "Angola",
        "primary_color": "#EA580C",
        "secondary_color": "#FFFFFF",
        "email": "secretaria@cdhuila.ao",
        "phone": "+244 923 111 007",
        "website": "https://cdhuila.ao",
        "description": "Grande representante desportivo do sul de Angola sediado na cidade do Lubango.",
    },
    {
        "name": "Kabuscorp Sport Clube do Palanca",
        "slug": "kabuscorp",
        "short_name": "KAB",
        "founded_year": 1994,
        "stadium_name": "Estádio dos Coqueiros",
        "stadium_capacity": 12000,
        "city": "Luanda",
        "country": "Angola",
        "primary_color": "#DC2626",
        "secondary_color": "#FFFFFF",
        "email": "palanca@kabuscorp.ao",
        "phone": "+244 923 111 008",
        "website": "https://kabuscorp.ao",
        "description": "Clube muito popular do bairro Palanca em Luanda, campeão nacional de 2013.",
    },
]

COMPETITIONS_DATA = [
    {
        "name": "Girabola 2025/26",
        "slug": "girabola-2025-26",
        "season": "2025/26",
        "competition_type": CompetitionType.LEAGUE,
        "status": CompetitionStatus.ACTIVE,
    },
    {
        "name": "Taça de Angola 2025/26",
        "slug": "taca-de-angola-2025-26",
        "season": "2025/26",
        "competition_type": CompetitionType.CUP,
        "status": CompetitionStatus.ACTIVE,
    },
    {
        "name": "Supertaça de Angola 2025",
        "slug": "supertaca-de-angola-2025",
        "season": "2025",
        "competition_type": CompetitionType.CUP,
        "status": CompetitionStatus.COMPLETED,
    },
]

FIRST_NAMES = [
    "Aderito", "Agostinho", "Afonso", "Amado", "Andre", "Antonio", "Artur",
    "Bruno", "Carlos", "Dirceu", "Domingos", "Edson", "Ernesto", "Fabio",
    "Felipe", "Fernando", "Francisco", "Gelson", "Helder", "Jacinto",
    "Joao", "Jorge", "Jose", "Julio", "Luis", "Luiz", "Manuel", "Marco",
    "Mario", "Mateus", "Miguel", "Nuno", "Osvaldo", "Paulo", "Pedro",
    "Renato", "Ricardo", "Rui", "Sergio", "Silvestre", "Tiago", "Welton",
    "Zito", "Dalcio", "Dilson", "Eustaquio", "Feliciano", "Gilberto", "Bastos",
    "Fredy", "Show", "Mabululu", "Zine", "Neblu", "Kinito", "Eddie",
]

LAST_NAMES = [
    "Almeida", "Alves", "Andrade", "Baptista", "Barros", "Campos", "Cardoso",
    "Carvalho", "Castro", "Coelho", "Correia", "Costa", "Cunha", "Dias",
    "Faria", "Fernandes", "Ferreira", "Fonseca", "Freitas", "Gomes", "Leal",
    "Lopes", "Macedo", "Martins", "Matos", "Mendes", "Monteiro", "Moura",
    "Nascimento", "Neto", "Neves", "Oliveira", "Paiva", "Pereira", "Pinto",
    "Ribeiro", "Rodrigues", "Santos", "Silva", "Sousa", "Tavares", "Teixeira",
    "Dala", "Quaresma", "Gaspar", "Carneiro", "Balbúrdia", "Luvumbo",
]

STAFF_ROLES = [
    (ClubMemberRole.COACH, "Treinador Principal"),
    (ClubMemberRole.ASSISTANT_COACH, "Treinador Adjunto"),
    (ClubMemberRole.PHYSIO, "Fisioterapeuta"),
    (ClubMemberRole.MANAGER, "Diretor Desportivo"),
]

NATIONALITIES = [
    "Angola", "Angola", "Angola", "Angola", "Angola", "Angola",
    "Brasil", "Portugal", "Moçambique", "RD Congo", "Zâmbia", "Namíbia",
]

POSITION_TEMPLATE = [
    ("gk", 3),
    ("cb", 4),
    ("lb", 2),
    ("rb", 2),
    ("lwb", 1),
    ("rwb", 1),
    ("cdm", 2),
    ("cm", 3),
    ("cam", 2),
    ("lw", 2),
    ("rw", 2),
    ("st", 3),
    ("cf", 1),
]

FEET = ["right", "right", "right", "left", "both"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def random_dob(min_age: int = 17, max_age: int = 37) -> datetime.date:
    today = datetime.date.today()
    year = today.year - random.randint(min_age, max_age)
    return datetime.date(year, random.randint(1, 12), random.randint(1, 28))


def generate_avatar_url(name: str, bg_color: str = "014D40") -> str:
    bg_clean = bg_color.lstrip("#")
    name_encoded = urllib.parse.quote(name)
    return f"https://ui-avatars.com/api/?name={name_encoded}&background={bg_clean}&color=fff&size=256&bold=true&format=png"


def build_position_list(count: int) -> List[str]:
    pool = []
    for pos, qty in POSITION_TEMPLATE:
        pool.extend([pos] * qty)
    while len(pool) < count:
        pool.append(random.choice(["cm", "cb", "st", "lw", "rw"]))
    random.shuffle(pool)
    return pool[:count]


# ── Ecosystem Seeder ─────────────────────────────────────────────────────────

class EcosystemSeeder:
    def __init__(
        self,
        user_email: Optional[str] = None,
        clubs_per_org: int = 6,
        players_per_club: int = 22,
        matches_per_comp: int = 6,
        dry_run: bool = False,
    ):
        self.user_email = user_email
        self.clubs_per_org = clubs_per_org
        self.players_per_club = players_per_club
        self.matches_per_comp = matches_per_comp
        self.dry_run = dry_run

        self.stats = {
            "tenants": 0,
            "clubs": 0,
            "staff": 0,
            "players": 0,
            "registrations": 0,
            "competitions": 0,
            "competition_registrations": 0,
            "standings": 0,
            "matches": 0,
        }

    def log(self, message: str, level: str = "info") -> None:
        prefix = {
            "info": "  [INFO] ",
            "success": "  [OK]   ",
            "warn": "  [WARN] ",
            "head": ">>> ",
        }.get(level, "  ")
        print(f"{prefix}{message}")

    def get_or_resolve_user(self) -> Optional[User]:
        if self.user_email:
            user = User.objects.filter(email=self.user_email).first()
            if user:
                self.log(f"Utilizador fornecido encontrado: {user.email} (ID={user.id})", "success")
                return user
            else:
                self.log(f"Utilizador '{self.user_email}' não encontrado. A tentar primeiro utilizador ativo...", "warn")

        # Fallback to any existing user or admin
        user = User.objects.filter(is_active=True).first()
        if user:
            self.log(f"Utilizador associado para gestão: {user.email}", "info")
            return user

        self.log("Nenhum utilizador encontrado na base de dados. O ecossistema será criado sem vínculo de utilizador.", "warn")
        return None

    def clean_existing_mock_data(self) -> None:
        self.log("A limpar dados anteriores gerados por mock...", "warn")
        with transaction.atomic():
            # Clean competitions created by mock
            mock_comp_slugs = [c["slug"] for c in COMPETITIONS_DATA]
            deleted_comps = Competition.objects.filter(slug__in=mock_comp_slugs).delete()
            self.log(f"Competições limpas: {deleted_comps[0]} registos apagados.")

            # Clean clubs created by mock
            mock_club_slugs = [c["slug"] for c in CLUBS_DATA]
            deleted_clubs = Club.objects.filter(slug__in=mock_club_slugs).delete()
            self.log(f"Clubes limpos: {deleted_clubs[0]} registos apagados.")

            # Clean organizations created by mock
            mock_org_slugs = [o["slug"] for o in ORGANIZATIONS_DATA]
            deleted_orgs = Tenant.objects.filter(slug__in=mock_org_slugs).delete()
            self.log(f"Organizações limpas: {deleted_orgs[0]} registos apagados.")

    def seed_organizations(self, admin_user: Optional[User]) -> List[Tenant]:
        self.log("A criar Organizações (Tenants)...", "head")
        created_orgs = []

        for org_data in ORGANIZATIONS_DATA:
            slug = org_data["slug"]
            tenant, created = Tenant.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": org_data["name"],
                    "type": org_data["type"],
                    "subdomain": org_data["subdomain"],
                    "primary_color": org_data["primary_color"],
                    "secondary_color": org_data["secondary_color"],
                    "city": org_data["city"],
                    "country": org_data["country"],
                    "email": org_data["email"],
                    "phone": org_data["phone"],
                    "website": org_data["website"],
                    "description": org_data["description"],
                },
            )
            created_orgs.append(tenant)
            self.stats["tenants"] += 1 if created else 0
            status_text = "Criada" if created else "Já existia"
            self.log(f"{status_text}: {tenant.name} (subdomínio={tenant.subdomain})", "success")

            # Link admin user if present
            if admin_user:
                TenantMembership.objects.get_or_create(
                    user=admin_user,
                    tenant=tenant,
                    defaults={"role": MembershipRole.ADMIN, "is_active": True},
                )

        return created_orgs

    def seed_clubs_and_squads(self, organizations: List[Tenant], admin_user: Optional[User]) -> List[Club]:
        self.log("A criar Clubes, Equipas Técnicas e Plantéis...", "head")
        primary_tenant = organizations[0] if organizations else None
        if not primary_tenant:
            self.log("Nenhuma organização disponível para anexar clubes.", "warn")
            return []

        created_clubs = []
        club_defs = CLUBS_DATA[: self.clubs_per_org]

        for idx, club_info in enumerate(club_defs):
            # Alternate tenants across organizations if more than one
            assigned_tenant = organizations[idx % len(organizations)]
            slug = club_info["slug"]

            club, created = Club.objects.get_or_create(
                slug=slug,
                tenant=assigned_tenant,
                defaults={
                    "name": club_info["name"],
                    "short_name": club_info["short_name"],
                    "founded_year": club_info["founded_year"],
                    "stadium_name": club_info["stadium_name"],
                    "stadium_capacity": club_info["stadium_capacity"],
                    "city": club_info["city"],
                    "country": club_info["country"],
                    "primary_color": club_info["primary_color"],
                    "secondary_color": club_info["secondary_color"],
                    "email": club_info["email"],
                    "phone": club_info["phone"],
                    "website": club_info["website"],
                    "description": club_info["description"],
                    "is_public": True,
                    "is_verified": True,
                    "status": "active",
                },
            )
            created_clubs.append(club)
            self.stats["clubs"] += 1 if created else 0
            self.log(f"Clube: {club.name} ({assigned_tenant.name})", "success")

            # Associate admin user with the first club (Petro de Luanda)
            if admin_user and idx == 0:
                ClubMember.objects.get_or_create(
                    user=admin_user,
                    club=club,
                    defaults={
                        "role": ClubMemberRole.MANAGER,
                        "full_name": admin_user.get_full_name() or "Gestor Principal",
                        "is_active": True,
                    },
                )
                self.log(f"-> Utilizador {admin_user.email} associado como Gestor de {club.name}", "info")

            # Seed staff for this club
            self.seed_club_staff(club)

            # Seed squad players for this club
            self.seed_club_players(club)

        return created_clubs

    def seed_club_staff(self, club: Club) -> None:
        for role, default_title in STAFF_ROLES:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            avatar = generate_avatar_url(full_name, club.primary_color)

            member, created = ClubMember.objects.get_or_create(
                club=club,
                role=role,
                defaults={
                    "full_name": full_name,
                    "is_active": True,
                    "joined_at": datetime.date(2025, 8, 1),
                },
            )
            if created:
                self.stats["staff"] += 1

    def seed_club_players(self, club: Club) -> None:
        positions = build_position_list(self.players_per_club)
        used_shirts = set(
            PlayerRegistration.objects.filter(club=club)
            .exclude(shirt_number__isnull=True)
            .values_list("shirt_number", flat=True)
        )

        for i, pos in enumerate(positions, start=1):
            # Select unique shirt number (1-99)
            shirt = next((n for n in range(1, 100) if n not in used_shirts), None)
            if shirt:
                used_shirts.add(shirt)

            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            nat = random.choice(NATIONALITIES)
            dob = random_dob()
            foot = random.choice(FEET)

            # Assign realistic performance metrics based on position
            is_forward = pos in ["st", "cf", "lw", "rw"]
            is_mid = pos in ["cm", "cam", "cdm", "lm", "rm"]
            is_gk = pos == "gk"

            matches_played = random.randint(12, 28)
            goals = random.randint(4, 18) if is_forward else (random.randint(1, 7) if is_mid else 0)
            assists = random.randint(3, 12) if (is_forward or is_mid) else random.randint(0, 2)
            yellows = random.randint(0, 2) if is_gk else random.randint(1, 6)
            reds = 1 if random.random() < 0.15 else 0

            # Status distribution: 85% registered/active, 10% loaned, 5% suspended
            roll = random.random()
            if roll < 0.85:
                reg_status = PlayerRegistration.RegistrationStatus.REGISTERED
            elif roll < 0.95:
                reg_status = PlayerRegistration.RegistrationStatus.LOANED
            else:
                reg_status = PlayerRegistration.RegistrationStatus.SUSPENDED

            avatar_url = generate_avatar_url(full_name, club.primary_color)

            # Generate or find Player
            player_slug = slugify(f"{first}-{last}-{random.randint(100, 9999)}")
            player = Player.objects.create(
                first_name=first,
                last_name=last,
                slug=player_slug,
                date_of_birth=dob,
                nationality=nat,
                primary_position=pos,
                shirt_number=shirt,
                height_cm=random.randint(168, 196),
                weight_kg=random.randint(66, 91),
                foot=foot,
                avatar=avatar_url,
                status=Player.PlayerStatus.ACTIVE,
                is_public=True,
            )
            self.stats["players"] += 1

            # Register player with club
            PlayerRegistration.objects.create(
                player=player,
                club=club,
                tenant=club.tenant,
                shirt_number=shirt,
                joined_date=datetime.date(2025, random.randint(1, 9), random.randint(1, 28)),
                status=reg_status,
                matches_played=matches_played,
                goals=goals,
                assists=assists,
                yellow_cards=yellows,
                red_cards=reds,
            )
            self.stats["registrations"] += 1

    def seed_competitions_and_fixtures(self, organizations: List[Tenant], clubs: List[Club]) -> None:
        self.log("A criar Competições, Classificações e Jogos...", "head")
        if not organizations or not clubs:
            return

        for org in organizations:
            for comp_info in COMPETITIONS_DATA:
                comp_slug = f"{comp_info['slug']}-{org.slug}"
                competition, created = Competition.objects.get_or_create(
                    tenant=org,
                    slug=comp_slug,
                    season=comp_info["season"],
                    defaults={
                        "name": f"{comp_info['name']} ({org.slug.upper()})",
                        "competition_type": comp_info["competition_type"],
                        "status": comp_info["status"],
                    },
                )
                self.stats["competitions"] += 1 if created else 0
                self.log(f"Competição: {competition.name}", "success")

                # Register all clubs of this organization (or all available clubs)
                org_clubs = [c for c in clubs if c.tenant_id == org.id]
                participating_clubs = org_clubs if len(org_clubs) >= 2 else clubs

                for club in participating_clubs:
                    CompetitionRegistration.objects.get_or_create(
                        competition=competition,
                        club=club,
                        tenant=org,
                    )
                    self.stats["competition_registrations"] += 1

                # Generate Standings table for leagues
                if competition.competition_type == CompetitionType.LEAGUE and participating_clubs:
                    self.seed_standings(competition, org, participating_clubs)

                # Generate sample match fixtures
                if participating_clubs and len(participating_clubs) >= 2:
                    self.seed_matches(competition, org, participating_clubs)

    def seed_standings(self, competition: Competition, tenant: Tenant, clubs: List[Club]) -> None:
        # Generate varied points and goal differences for realistic table
        shuffled = list(clubs)
        random.shuffle(shuffled)

        for pos, club in enumerate(shuffled, start=1):
            played = random.randint(10, 18)
            # Upper ranked clubs win more
            bias = len(shuffled) - pos
            won = max(0, min(played, int(played * 0.4 + (bias * 0.6))))
            lost = max(0, min(played - won, int((pos * 0.5))))
            drawn = max(0, played - won - lost)

            goals_for = won * 2 + drawn * 1 + random.randint(2, 10)
            goals_against = lost * 2 + drawn * 1 + random.randint(1, 5)
            goal_diff = goals_for - goals_against
            points = (won * 3) + drawn

            Standing.objects.update_or_create(
                tenant=tenant,
                competition=competition,
                club=club,
                defaults={
                    "position": pos,
                    "played": played,
                    "won": won,
                    "drawn": drawn,
                    "lost": lost,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "goal_difference": goal_diff,
                    "points": points,
                },
            )
            self.stats["standings"] += 1

    def seed_matches(self, competition: Competition, tenant: Tenant, clubs: List[Club]) -> None:
        # Create rounds of matches
        now = timezone.now()
        pairs = []
        club_list = list(clubs)
        random.shuffle(club_list)

        for i in range(0, len(club_list) - 1, 2):
            pairs.append((club_list[i], club_list[i + 1]))

        # Create finished matches in the past
        for round_num in range(1, 3):
            for home, away in pairs[: self.matches_per_comp]:
                match_time = now - datetime.timedelta(days=(3 - round_num) * 7, hours=random.randint(15, 19))
                home_score = random.randint(0, 3)
                away_score = random.randint(0, 2)

                Match.objects.get_or_create(
                    competition=competition,
                    tenant=tenant,
                    home_club=home,
                    away_club=away,
                    round_number=round_num,
                    defaults={
                        "match_date": match_time,
                        "round_name": f"Jornada {round_num}",
                        "status": Match.MatchStatus.FINISHED,
                        "home_score": home_score,
                        "away_score": away_score,
                        "venue": home.stadium_name or "Estádio Municipal",
                    },
                )
                self.stats["matches"] += 1

        # Create upcoming scheduled match in the future
        for home, away in pairs[: self.matches_per_comp]:
            upcoming_time = now + datetime.timedelta(days=random.randint(3, 14), hours=16)
            Match.objects.get_or_create(
                competition=competition,
                tenant=tenant,
                home_club=home,
                away_club=away,
                round_number=4,
                defaults={
                    "match_date": upcoming_time,
                    "round_name": "Jornada 4",
                    "status": Match.MatchStatus.SCHEDULED,
                    "venue": home.stadium_name or "Estádio Municipal",
                },
            )
            self.stats["matches"] += 1

    def run(self, clean: bool = False) -> None:
        print("\n" + "=" * 70)
        print("  BOLAYETU - GERADOR DE DADOS MOCK DO ECOSSISTEMA")
        print("  Organizacoes * Clubes * Jogadores * Competicoes * Jogos")
        print("=" * 70 + "\n")

        if self.dry_run:
            self.log("[DRY RUN ATIVADO] Simulacao sem gravacao no banco de dados.", "warn")
            return

        if clean:
            self.clean_existing_mock_data()

        admin_user = self.get_or_resolve_user()

        with transaction.atomic():
            # 1. Seed Organizations
            orgs = self.seed_organizations(admin_user)

            # 2. Seed Clubs and Squads
            clubs = self.seed_clubs_and_squads(orgs, admin_user)

            # 3. Seed Competitions, Standings and Matches
            self.seed_competitions_and_fixtures(orgs, clubs)

        print("\n" + "=" * 70)
        print("  RESUMO DA EXECUCAO")
        print("=" * 70)
        print(f"  Organizacoes (Tenants) criadas : {self.stats['tenants']}")
        print(f"  Clubes criados                 : {self.stats['clubs']}")
        print(f"  Membros de Staff criados       : {self.stats['staff']}")
        print(f"  Jogadores criados              : {self.stats['players']}")
        print(f"  Inscricoes de Atletas (Squad)  : {self.stats['registrations']}")
        print(f"  Competicoes criadas            : {self.stats['competitions']}")
        print(f"  Clubes inscritos em provas     : {self.stats['competition_registrations']}")
        print(f"  Registos de Classificacao      : {self.stats['standings']}")
        print(f"  Partidas / Fixtures criadas    : {self.stats['matches']}")
        print("=" * 70)
        print("  Ecossistema pronto para visualizacao e testes no frontend!\n")


# ── Entrypoint ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera ecossistema completo de dados mock para o Bolayetu (Organizações, Clubes, Jogadores, Competições)."
    )
    parser.add_argument(
        "--user-email",
        type=str,
        default=None,
        help="Email do utilizador a associar como Gestor do Clube e Admin da Organização.",
    )
    parser.add_argument(
        "--clubs-per-org",
        type=int,
        default=6,
        help="Número de clubes a criar/vincular por organização (default: 6).",
    )
    parser.add_argument(
        "--players-per-club",
        type=int,
        default=22,
        help="Número de jogadores a criar no plantel de cada clube (default: 22).",
    )
    parser.add_argument(
        "--matches-per-comp",
        type=int,
        default=4,
        help="Número de jogos a simular por competição (default: 4).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Limpar dados mocks gerados anteriormente antes de criar novos.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sem persistir na base de dados.",
    )

    args = parser.parse_args()

    seeder = EcosystemSeeder(
        user_email=args.user_email,
        clubs_per_org=args.clubs_per_org,
        players_per_club=args.players_per_club,
        matches_per_comp=args.matches_per_comp,
        dry_run=args.dry_run,
    )

    seeder.run(clean=args.clean)


if __name__ == "__main__":
    main()
