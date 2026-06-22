# Deploy do Bolayetu em VPS Ubuntu com Gunicorn e Nginx

Este guia descreve um fluxo recomendado para colocar o backend Django e o frontend Vite do Bolayetu em produção numa VPS Ubuntu acessível pela internet, usando:

- Python + virtualenv
- Gunicorn como WSGI server para o Django (`config.wsgi:application`)
- Nginx como reverse proxy (API + static/media + frontend buildado)

> Neste guia vamos assumir:
>
> - Frontend: `bolayetu.ndeas.cloud`
> - Backend/API: `api-bolayetu-manager.ndeas.cloud`
>
> Ajuste caminhos, credenciais e nomes de base de dados conforme o seu ambiente.

---

## 1. Pré‑requisitos

Servidor:

- Ubuntu 22.04 LTS (ou superior)
- Acesso SSH com utilizador com permissões `sudo` (assumimos utilizador `deploy`)
- Domínio(s) DNS apontando para o IP público da VPS

Pacotes base:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git
```

Instalar PostgreSQL:

```bash
sudo apt install -y postgresql postgresql-contrib
```

Se for fazer o build do frontend na própria VM:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

Firewall (se usar `ufw`):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 2. Obter o código e preparar estrutura

Escolha um diretório para alojar o projeto, por exemplo `/var/www/bolayetu` (comandos executados como utilizador `deploy`):

```bash
sudo mkdir -p /var/www/bolayetu
sudo chown -R deploy:deploy /var/www/bolayetu
cd /var/www/bolayetu

git clone <URL_DO_REPO> .
```

Estrutura esperada:

- `/var/www/bolayetu/backend` – projeto Django (onde está o `manage.py`)
- `/var/www/bolayetu/frontend` – frontend Vite/React

---

## 3. Configuração do backend (Django)

Entrar na pasta do backend e criar virtualenv:

```bash
cd /var/www/bolayetu/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.1. Ajustar `settings.py` para produção

Ficheiro: `backend/config/settings.py`

Principais parâmetros controlados por variáveis de ambiente:

- `SECRET_KEY` ← `DJANGO_SECRET_KEY`
- `DEBUG` ← `DJANGO_DEBUG`
- `ALLOWED_HOSTS` ← `DJANGO_ALLOWED_HOSTS`
- Base de dados PostgreSQL ← `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- CORS ← `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOWED_ORIGINS`
- URLs e email ← `FRONTEND_URL`, `DEFAULT_FROM_EMAIL`
- Integrações externas ← `MCX_API_URL`, `UNITEL_API_URL`

Em desenvolvimento, pode deixar o `.env` próximo de:

```env
DJANGO_SECRET_KEY=change-me-to-a-strong-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=bolayetu
POSTGRES_USER=bolayetu_user
POSTGRES_PASSWORD=change-me-db-password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
FRONTEND_URL=http://localhost:5173
DEFAULT_FROM_EMAIL=no-reply@bolayetu.local
CORS_ALLOW_ALL_ORIGINS=True
MCX_API_URL=MOCK
UNITEL_API_URL=MOCK
```

Em produção na VPS (por exemplo via systemd), uma configuração típica é:

```env
DJANGO_SECRET_KEY=uma_chave_bem_grande_e_secreta
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api-bolayetu-manager.ndeas.cloud,localhost
POSTGRES_DB=bolayetu
POSTGRES_USER=bolayetu_user
POSTGRES_PASSWORD=senha_forte_aqui
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
FRONTEND_URL=https://bolayetu.ndeas.cloud
DEFAULT_FROM_EMAIL=no-reply@bolayetu.ndeas.cloud
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://bolayetu.ndeas.cloud
MCX_API_URL=MOCK
UNITEL_API_URL=MOCK
```

### 3.2. Migrar base de dados e recolher estáticos

Ainda em `/var/www/bolayetu/backend` com a venv ativa:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Por omissão:

- `STATIC_ROOT = BASE_DIR / 'staticfiles'`
- `MEDIA_ROOT = BASE_DIR / 'media'`

### 3.3. Configurar PostgreSQL

Criar base de dados e utilizador:

```bash
sudo -u postgres psql

CREATE DATABASE bolayetu;
CREATE USER bolayetu_user WITH PASSWORD 'senha_forte_aqui';
ALTER ROLE bolayetu_user SET client_encoding TO 'utf8';
ALTER ROLE bolayetu_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bolayetu_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE bolayetu TO bolayetu_user;
\q
```

No `config/settings.py`, substituir a configuração padrão de SQLite por PostgreSQL (exemplo usando variáveis de ambiente com defaults razoáveis):

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'bolayetu'),
        'USER': os.environ.get('POSTGRES_USER', 'bolayetu_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'senha_forte_aqui'),
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}
```

> Em produção, defina `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_HOST` no serviço systemd ou no ambiente da VPS.

---

## 4. Gunicorn como serviço systemd

Instalar Gunicorn na virtualenv (se necessário):

```bash
cd /var/www/bolayetu/backend
source .venv/bin/activate
pip install gunicorn
deactivate
```

Criar serviço systemd:

```bash
sudo nano /etc/systemd/system/bolayetu.service
```

Conteúdo sugerido (com variáveis de ambiente alinhadas com `config/settings.py`):

```ini
[Unit]
Description=BolaYetu Django Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/bolayetu/backend
Environment="PATH=/var/www/bolayetu/backend/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
Environment="DJANGO_SECRET_KEY=uma_chave_bem_grande_e_secreta"
Environment="DJANGO_DEBUG=False"
Environment="DJANGO_ALLOWED_HOSTS=api-bolayetu-manager.ndeas.cloud,localhost"
Environment="POSTGRES_DB=bolayetu"
Environment="POSTGRES_USER=bolayetu_user"
Environment="POSTGRES_PASSWORD=senha_forte_aqui"
Environment="POSTGRES_HOST=127.0.0.1"
Environment="POSTGRES_PORT=5432"
Environment="FRONTEND_URL=https://bolayetu.ndeas.cloud"
Environment="DEFAULT_FROM_EMAIL=no-reply@bolayetu.ndeas.cloud"
Environment="CORS_ALLOW_ALL_ORIGINS=False"
Environment="CORS_ALLOWED_ORIGINS=https://bolayetu.ndeas.cloud"
Environment="MCX_API_URL=MOCK"
Environment="UNITEL_API_URL=MOCK"

ExecStart=/var/www/bolayetu/backend/.venv/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8001 \
  config.wsgi:application

Restart=always
KillSignal=SIGQUIT
TimeoutStopSec=5
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

Ativar e iniciar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bolayetu
sudo systemctl start bolayetu
sudo systemctl status bolayetu
```

Logs em caso de erro:

```bash
journalctl -u bolayetu -xe
```

---

## 5. Nginx para API, static e media

Criar configuração do site:

```bash
sudo nano /etc/nginx/sites-available/bolayetu
```

Exemplo mínimo focado na API e ficheiros do backend (domínio `api-bolayetu-manager.ndeas.cloud`):

```nginx
server {
    listen 80;
    server_name api-bolayetu-manager.ndeas.cloud;

    # Static files gerados pelo collectstatic
    location /static/ {
        alias /var/www/bolayetu/backend/staticfiles/;
    }

    # Media files (uploads)
    location /media/ {
        alias /var/www/bolayetu/backend/media/;
    }

    # API Django exposta em /api/ via Gunicorn
    location /api/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_pass http://127.0.0.1:8001;
    }
}
```

Ativar o site e recarregar:

```bash
sudo ln -s /etc/nginx/sites-available/bolayetu /etc/nginx/sites-enabled/bolayetu
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Deploy do frontend (Vite)

No servidor:

```bash
cd /var/www/bolayetu/frontend
npm ci           # ou npm install
npm run build    # gera dist/
```

Pasta de output: `/var/www/bolayetu/frontend/dist`.

Atualizar o `server` Nginx para servir o frontend no domínio `bolayetu.ndeas.cloud`:

```nginx
server {
    listen 80;
    server_name bolayetu.ndeas.cloud;

    root /var/www/bolayetu/frontend/dist;

    # SPA: devolver sempre index.html para rotas desconhecidas
    location / {
        try_files $uri /index.html;
    }
}
```

Validar e recarregar:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Checklist de pós‑deploy

1. **Django**
   - `DEBUG = False` em `config/settings.py`.
   - `ALLOWED_HOSTS` configurado corretamente.
   - `python manage.py check --deploy` sem erros críticos.
   - `python manage.py migrate` executado.
   - `python manage.py collectstatic --noinput` executado e `/static/` acessível pelo browser.

2. **Gunicorn**
   - Serviço `bolayetu` ativo: `systemctl status bolayetu`.
   - Logs limpos de erros relevantes: `journalctl -u bolayetu -xe`.

3. **Nginx**
   - `nginx -t` sem erros.
   - `systemctl status nginx` `active (running)`.
   - Acesso à aplicação pela URL pública (via DNS) funciona.
   - Endpoints `/api/...` respondem corretamente (ex.: `/api/docs/` se ativado).

4. **Frontend**
   - `npm run build` foi executado.
   - Rotas públicas (landing, torneios públicos, notícias, etc.) funcionam diretamente via URL.

---

## 8. Notas e extensões possíveis

- **HTTPS/Let's Encrypt**: em produção pública na VPS, configure certificados reais (por exemplo via Certbot/Let's Encrypt) e atualize os `server` Nginx para `listen 443 ssl` e respetivas diretivas `ssl_certificate`.

  Exemplo rápido com Certbot para Nginx:

  ```bash
  sudo apt update
  sudo apt install -y certbot python3-certbot-nginx

  # Gerar e configurar certificados para os domínios da API e frontend
  sudo certbot --nginx -d api-bolayetu-manager.ndeas.cloud -d bolayetu.ndeas.cloud

  # Validar configuração e recarregar Nginx (Certbot normalmente faz isto automaticamente)
  sudo nginx -t
  sudo systemctl reload nginx

  # Verificar agendamento de renovação automática
  sudo systemctl status certbot.timer
  ```

  Depois de o Certbot ajustar os blocos `server`, confirme que:

  - As portas 80 e 443 estão abertas na firewall da VPS.
  - O redirecionamento HTTP→HTTPS está a funcionar.
  - Os certificados aparecem válidos no browser (cadeia completa).
- **Logs e monitoring**:
  - Usar `access_log` e `error_log` no Nginx ajustados para o ambiente.
  - Configurar logging do Django para ficheiros separados se necessário.
- **Atualizações de versão**:
  - Pull da nova versão em `/var/www/bolayetu`.
  - Reinstalar dependências se necessário (`pip install -r requirements.txt`, `npm ci`).
  - Executar `migrate` e `collectstatic`.
  - `sudo systemctl restart bolayetu` e `sudo systemctl reload nginx`.
