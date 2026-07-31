"""
BOLAYETU -- Seed Mock Players

Cria jogadores (Player) mock e registra-os num clube via PlayerRegistration.

Uso no PowerShell (Windows):
    cd bybackend
    python scripts/seed_mock_players.py --club-slug="santos-de-luanda"
    python scripts/seed_mock_players.py --club-slug="santos-de-luanda" --count=30
    python scripts/seed_mock_players.py --club-slug="santos-de-luanda" --dry-run

Uso no Bash/Linux:
    python scripts/seed_mock_players.py --club-slug=primeiro-de-agosto --count=25

Argumentos:
    --club-slug   Slug do clube alvo (obrigatorio)
    --count       Numero de jogadores a criar (default: 25)
    --year        Ano da temporada (default: 2026)
    --dry-run     Simular sem salvar
    --list-clubs  Listar todos os clubes e sair
"""

import os
import sys
import random
import datetime
import argparse

# ── Django bootstrap ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

# ── Imports Django ─────────────────────────────────────────────────────────────
from clubs.models import Club
from players.models import Player, PlayerRegistration

# ── Dados de Mock ──────────────────────────────────────────────────────────────
FIRST_NAMES_M = [
    "Aderito", "Agostinho", "Afonso", "Amado", "Andre", "Antonio", "Artur",
    "Bruno", "Carlos", "Dirceu", "Domingos", "Edson", "Ernesto", "Fabio",
    "Felipe", "Fernando", "Francisco", "Gelson", "Helder", "Jacinto",
    "Joao", "Jorge", "Jose", "Julio", "Luis", "Luiz", "Manuel", "Marco",
    "Mario", "Mateus", "Miguel", "Nuno", "Osvaldo", "Paulo", "Pedro",
    "Renato", "Ricardo", "Rui", "Sergio", "Silvestre", "Tiago", "Welton",
    "Zito", "Dalcio", "Dilson", "Eustaquio", "Feliciano",
]

LAST_NAMES = [
    "Almeida", "Alves", "Andrade", "Baptista", "Barros", "Campos", "Cardoso",
    "Carvalho", "Castro", "Coelho", "Correia", "Costa", "Cunha", "Dias",
    "Faria", "Fernandes", "Ferreira", "Fonseca", "Freitas", "Gomes", "Leal",
    "Lopes", "Macedo", "Martins", "Matos", "Mendes", "Monteiro", "Moura",
    "Nascimento", "Neto", "Neves", "Oliveira", "Paiva", "Pereira", "Pinto",
    "Ribeiro", "Rodrigues", "Santos", "Silva", "Sousa", "Tavares", "Teixeira",
]

NATIONALITIES = [
    "Angola", "Angola", "Angola", "Angola", "Angola", "Angola",
    "Brasil", "Portugal", "Mocambique", "Congo", "Namibia", "Zambia",
]

POSITION_POOL_TEMPLATE = [
    ("gk",  3),
    ("cb",  4),
    ("lb",  2),
    ("rb",  2),
    ("lwb", 1),
    ("rwb", 1),
    ("cdm", 2),
    ("cm",  3),
    ("cam", 2),
    ("lw",  2),
    ("rw",  2),
    ("st",  3),
    ("cf",  2),
]

FEET = ["right", "right", "right", "left", "both"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def random_dob(min_age: int = 17, max_age: int = 38) -> datetime.date:
    today = datetime.date.today()
    year = today.year - random.randint(min_age, max_age)
    return datetime.date(year, random.randint(1, 12), random.randint(1, 28))


def build_position_pool(total: int) -> list:
    pool = []
    for code, qty in POSITION_POOL_TEMPLATE:
        pool.extend([code] * qty)
    while len(pool) < total:
        pool.append(random.choice(["cm", "st", "cb"]))
    random.shuffle(pool)
    return pool[:total]


def unique_email(first: str, last: str, used: set):
    base = f"{first.lower()}.{last.lower()}@bolayetu.mock"
    email, n = base, 1
    while email in used:
        email = f"{first.lower()}.{last.lower()}{n}@bolayetu.mock"
        n += 1
    used.add(email)
    return email


def list_clubs() -> None:
    clubs = Club.objects.all().order_by("name")
    if not clubs.exists():
        print("  Nenhum clube encontrado na base de dados.")
        return
    print(f"\n  {'SLUG':<40} NOME")
    print(f"  {'-'*40} {'-'*30}")
    for c in clubs:
        print(f"  {c.slug:<40} {c.name}")
    print()


# ── Seed ──────────────────────────────────────────────────────────────────────

def seed(club: Club, player_count: int, season_year: int, dry_run: bool) -> None:
    print(f"\n{'='*60}")
    print(f"  Clube      : {club.name}  (slug={club.slug})")
    print(f"  Jogadores  : {player_count}")
    print(f"  Temporada  : {season_year}")
    print(f"  Dry run    : {dry_run}")
    print(f"{'='*60}\n")

    existing = PlayerRegistration.objects.filter(
        club=club, status=PlayerRegistration.RegistrationStatus.REGISTERED
    ).count()
    print(f"  Registos existentes no clube: {existing}\n")

    positions  = build_position_pool(player_count)
    used_emails: set = set()
    used_shirts: set = set(
        PlayerRegistration.objects.filter(club=club)
        .exclude(shirt_number__isnull=True)
        .values_list("shirt_number", flat=True)
    )

    created_players, created_regs = [], []

    for i, pos in enumerate(positions, start=1):
        first = random.choice(FIRST_NAMES_M)
        last  = random.choice(LAST_NAMES)
        nat   = random.choice(NATIONALITIES)
        dob   = random_dob()
        foot  = random.choice(FEET)
        email = unique_email(first, last, used_emails) if random.random() > 0.4 else None

        shirt = next((n for n in range(1, 100) if n not in used_shirts), None)
        if shirt:
            used_shirts.add(shirt)

        print(f"  [{i:02d}] {first} {last:<22} | {pos.upper():<4} "
              f"| #{str(shirt):<2} | {nat:<12} | {dob} | pe={foot}")

        if dry_run:
            continue

        player = Player.objects.create(
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            nationality=nat,
            primary_position=pos,
            shirt_number=shirt,
            height_cm=random.randint(165, 196),
            weight_kg=random.randint(65, 92),
            foot=foot,
            email=email,
            status=Player.PlayerStatus.ACTIVE,
            is_public=True,
        )
        created_players.append(player)

        reg = PlayerRegistration.objects.create(
            player=player,
            club=club,
            tenant=club.tenant,
            shirt_number=shirt,
            joined_date=datetime.date(season_year, 1, 15),
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
        )
        created_regs.append(reg)

    print(f"\n{'='*60}")
    if dry_run:
        print(f"  [DRY RUN] {player_count} jogadores simulados — nada foi salvo.")
    else:
        print(f"  Criados  : {len(created_players)} jogadores")
        print(f"  Registos : {len(created_regs)} em '{club.name}'")
    print(f"{'='*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera jogadores mock e regista-os num clube Bolayetu."
    )
    parser.add_argument(
        "--club-slug", "-c",
        required=False,
        default="",
        help="Slug do clube alvo (ex: santos-de-luanda)",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=25,
        help="Numero de jogadores a criar (default: 25)",
    )
    parser.add_argument(
        "--year", "-y",
        type=int,
        default=2026,
        help="Ano da temporada (default: 2026)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sem salvar na base de dados",
    )
    parser.add_argument(
        "--list-clubs",
        action="store_true",
        help="Listar todos os clubes disponiveis e sair",
    )

    args = parser.parse_args()

    if args.list_clubs:
        list_clubs()
        return

    if not args.club_slug:
        print("\n  [ERRO] Tens de indicar o slug do clube com --club-slug")
        print("  Usa --list-clubs para ver os slugs disponiveis.\n")
        parser.print_help()
        sys.exit(1)

    try:
        club = Club.objects.get(slug=args.club_slug)
    except Club.DoesNotExist:
        print(f"\n  [ERRO] Clube com slug '{args.club_slug}' nao encontrado.")
        list_clubs()
        sys.exit(1)

    seed(club, player_count=args.count, season_year=args.year, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
