# BOLAYETU Backend

Football Ecosystem Platform - Backend API

## Fase 1 - Arquitetura, Autenticação e Multi-Tenant ✅

### Estrutura Implementada

```
backend/
├── config/                 # Configuração Django
│   ├── settings.py         # Settings principais
│   ├── urls.py             # URLs principais
│   └── wsgi.py             # WSGI config
├── common/                 # Utilitários base
│   ├── base.py             # BaseService, BaseSelector
│   └── exceptions.py       # Exception handler customizado
├── core/                   # Core models
│   └── models.py           # Tenant (Multi-tenant)
├── accounts/               # Autenticação
│   ├── models.py           # User customizado
│   ├── serializers.py      # Auth serializers
│   ├── views.py            # Auth views
│   └── urls.py             # Auth URLs
└── manage.py
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/auth/register/` | POST | Registar novo usuário |
| `/api/v1/auth/login/` | POST | Login (retorna JWT) |
| `/api/v1/auth/logout/` | POST | Logout (blacklist token) |
| `/api/v1/auth/me/` | GET/PUT | Perfil do usuário |
| `/api/v1/auth/change-password/` | POST | Alterar password |
| `/api/v1/auth/refresh/` | POST | Refresh token |
| `/api/docs/` | GET | Swagger UI |
| `/admin/` | GET | Django Admin |

### Testar a API

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bolayetu.com","password":"admin123"}'

# Resposta
{
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi...",
  "user": {...}
}
```

### Executar

```bash
# Ativar virtual environment
.\env\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Migrar base de dados
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Executar servidor
python manage.py runserver
```

### Credenciais de Teste

- **Email:** admin@bolayetu.com
- **Password:** admin123

### Próximos Passos (Roadmap)

- ✅ Fase 1: Arquitetura, Autenticação, Multi-Tenant
- ⏳ Fase 2: Organizações
- ⏳ Fase 3: Clubes
- ⏳ Fase 4: Jogadores
- ⏳ Fase 5: Competições

### Stack Tecnológica

- Python 3.13
- Django 6.0
- Django REST Framework 3.16
- PostgreSQL (produção) / SQLite (desenvolvimento)
- JWT Authentication
- Docker Ready
