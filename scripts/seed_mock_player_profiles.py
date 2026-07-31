"""
BOLAYETU -- Seed Mock Player Profiles

Cria perfis completos de jogador (Player com bio, avatar, estatisticas)
e registra-os num clube via PlayerRegistration.

Uso no PowerShell (Windows):
    cd bybackend
    python scripts/seed_mock_player_profiles.py --club-slug="santos-de-luanda"
    python scripts/seed_mock_player_profiles.py --club-slug="primeiro-de-agosto" --count=30 --competition-slug="girabola-2026"
    python scripts/seed_mock_player_profiles.py --list-clubs
    python scripts/seed_mock_player_profiles.py --club-slug="petro-de-luanda" --dry-run

Argumentos:
    --club-slug         Slug do clube alvo (obrigatorio)
    --count             Numero de jogadores a criar (default: 25)
    --year              Ano da temporada (default: 2026)
    --competition-slug  Slug da competicao para vincular (opcional)
    --avatar-style      "initials" | "dicebear" | "none" (default: initials)
    --dry-run           Simular sem salvar
    --list-clubs        Listar todos os clubes e sair
"""

import os
import sys
import random
import datetime
import argparse
import urllib.parse

# ── Django bootstrap ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

# ── Imports Django ─────────────────────────────────────────────────────────────
from clubs.models import Club
from players.models import Player, PlayerRegistration

# ── Dados de mock ──────────────────────────────────────────────────────────────
FIRST_NAMES = [
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

POSITION_LABELS = {
    "gk":  "Guarda-redes",
    "cb":  "Defesa Central",
    "lb":  "Defesa Esquerda",
    "rb":  "Defesa Direita",
    "lwb": "Lateral Esquerda",
    "rwb": "Lateral Direita",
    "cdm": "Medio Defensivo",
    "cm":  "Medio",
    "cam": "Medio Ofensivo",
    "lw":  "Ala Esquerda",
    "rw":  "Ala Direita",
    "st":  "Avancado",
    "cf":  "Ponta de Lanca",
}

FEET = ["right", "right", "right", "left", "both"]

BIO_TEMPLATES = [
    "{name} e um {pos} com {age} anos de experiencia no futebol angolano. "
    "Formado nas camadas jovens, destaca-se pela leitura do jogo e lideranca.",

    "Jogador dedicado e tecnicamente solido, {name} ocupa a posicao de {pos} "
    "e ja representou varios clubes antes de chegar ao {club}.",

    "{name} iniciou a sua carreira futebolistica aos 14 anos "
    "e hoje e um dos pilares da equipa como {pos}.",

    "Com vasta experiencia no futebol nacional, {name} e conhecido pela sua "
    "consistencia e profissionalismo na posicao de {pos}.",

    "Nascido em Angola, {name} sonhava ser futebolista desde crianca. "
    "Hoje realiza esse sonho como {pos} no {club}.",
]


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


def make_avatar_url(full_name: str, style: str) -> str:
    if style == "none":
        return ""
    name_enc = urllib.parse.quote(full_name)
    if style == "dicebear":
        return (
            f"https://api.dicebear.com/7.x/initials/svg"
            f"?seed={name_enc}&backgroundColor=014D40&textColor=ffffff"
        )
    # default: initials via UI Avatars
    return (
        f"https://ui-avatars.com/api/?name={name_enc}"
        f"&background=014D40&color=fff&size=256&bold=true&format=png"
    )


def make_bio(name: str, pos_code: str, club_name: str, dob: datetime.date) -> str:
    today = datetime.date.today()
    age = today.year - dob.year
    pos_label = POSITION_LABELS.get(pos_code, pos_code.upper())
    return random.choice(BIO_TEMPLATES).format(
        name=name, pos=pos_label, club=club_name, age=age
    )


def make_stats() -> dict:
    matches = random.randint(0, 180)
    goals   = random.randint(0, max(0, matches // 4))
    assists = random.randint(0, max(0, matches // 5))
    return {"total_matches": matches, "total_goals": goals, "total_assists": assists}


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

def seed(
    club: Club,
    player_count: int,
    season_year: int,
    dry_run: bool,
    avatar_style: str,
    competition=None,
) -> None:
    print(f"\n{'='*65}")
    print(f"  Clube       : {club.name}  (slug={club.slug})")
    print(f"  Competicao  : {competition.name if competition else 'N/A'}")
    print(f"  Jogadores   : {player_count}")
    print(f"  Temporada   : {season_year}")
    print(f"  Avatar      : {avatar_style}")
    print(f"  Dry run     : {dry_run}")
    print(f"{'='*65}\n")

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
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"
        nat   = random.choice(NATIONALITIES)
        dob   = random_dob()
        foot  = random.choice(FEET)
        email = unique_email(first, last, used_emails) if random.random() > 0.3 else None
        stats = make_stats()

        shirt = next((n for n in range(1, 100) if n not in used_shirts), None)
        if shirt:
            used_shirts.add(shirt)

        avatar = make_avatar_url(name, avatar_style)
        bio    = make_bio(name, pos, club.name, dob)

        print(f"  [{i:02d}] {name:<30} | {pos.upper():<4} | #{str(shirt):<2} | {nat}")

        if dry_run:
            print(f"       avatar : {avatar[:70]}...")
            print(f"       bio    : {bio[:70]}...")
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
            bio=bio,
            avatar=avatar or None,
            status=Player.PlayerStatus.ACTIVE,
            is_public=True,
            total_matches=stats["total_matches"],
            total_goals=stats["total_goals"],
            total_assists=stats["total_assists"],
        )
        created_players.append(player)

        reg = PlayerRegistration.objects.create(
            player=player,
            club=club,
            tenant=club.tenant,
            competition=competition,
            shirt_number=shirt,
            joined_date=datetime.date(season_year, 1, 15),
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
            matches_played=stats["total_matches"] % 30,
            goals=stats["total_goals"] % 20,
            assists=stats["total_assists"] % 15,
        )
        created_regs.append(reg)

    print(f"\n{'='*65}")
    if dry_run:
        print(f"  [DRY RUN] {player_count} perfis simulados — nada foi salvo.")
    else:
        print(f"  Perfis criados   : {len(created_players)}")
        print(f"  Registos criados : {len(created_regs)} em '{club.name}'")
        if competition:
            print(f"  Competicao       : {competition.name}")
    print(f"{'='*65}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera perfis completos de jogadores mock e regista-os num clube Bolayetu."
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
        "--competition-slug",
        default="",
        help="Slug da competicao para vincular (opcional)",
    )
    parser.add_argument(
        "--avatar-style",
        choices=["initials", "dicebear", "none"],
        default="initials",
        help="Estilo do avatar (default: initials)",
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

    competition = None
    if args.competition_slug:
        try:
            from competitions.models import Competition
            competition = Competition.objects.get(slug=args.competition_slug)
        except Exception as exc:
            print(f"\n  [AVISO] Competicao '{args.competition_slug}' nao encontrada: {exc}")
            print("  Continuando sem vincular a competicao...\n")

    seed(
        club=club,
        player_count=args.count,
        season_year=args.year,
        dry_run=args.dry_run,
        avatar_style=args.avatar_style,
        competition=competition,
    )


if __name__ == "__main__":
    main()
