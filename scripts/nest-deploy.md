# Deploy on Hack Club Nest (systemd only)

Nest routes `gratefultime-v2.eesa.hackclub.app` → port `33540`. No Caddy.

**SSH as your Nest user (`eesa`), not root.**

| Item | Value |
|------|-------|
| SSH | `ssh eesa.hackclub.app` |
| URL | `https://gratefultime-v2.eesa.hackclub.app` |
| Port | `33540` |
| systemd | `gratefultime-v2-backend.service` |

## 1. Supabase

Run `supabase/schema.sql` in Supabase SQL Editor.

## 2. Clone + env

```bash
git clone https://github.com/eesazahed/gratefultime-v2-backend.git ~/gratefultime-v2-backend
cd ~/gratefultime-v2-backend
cp .env.example .env
nano .env
```

## 3. Install + start (systemd runs setup.sh)

```bash
chmod +x deploy/install.sh setup.sh
./deploy/install.sh
```

Or manually:

```bash
nano ~/.config/systemd/user/gratefultime-v2-backend.service
```

Use `deploy/gratefultime-v2-backend.service`, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now gratefultime-v2-backend
```

The service runs:

```bash
~/gratefultime-v2-backend/setup.sh 33540 --service
```

## 4. Verify

```bash
ss -tlnp | grep 33540

python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:33540/api/v1/').read().decode())"

python3 -c "import urllib.request; print(urllib.request.urlopen('https://gratefultime-v2.eesa.hackclub.app/api/v1/').read().decode())"
```

## 5. Mobile

```typescript
BaseUrl: "https://gratefultime-v2.eesa.hackclub.app"
UseLiveApi: true
```

## Updates

```bash
~/gratefultime-v2-backend/deploy/update.sh
```

## Local dev (your Mac)

```bash
./setup.sh 8000
```

Uses `--reload`. Production on Nest uses `setup.sh 33540 --service` via systemd.
