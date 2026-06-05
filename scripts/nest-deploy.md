# Deploy on Hack Club Nest (systemd + Caddy)

| Item | Value |
|------|-------|
| SSH | `eesa.hackclub.app` |
| Public URL | `https://gratefultime-v2.eesa.hackclub.app` |
| App port | `33540` (localhost only — Caddy proxies in) |

## 1. Supabase (browser, one-time)

Run `supabase/schema.sql` in the Supabase SQL Editor.

## 2. Clone + env (SSH)

```bash
ssh eesa.hackclub.app
git clone <your-repo-url> ~/gratefultime-v2-backend
cd ~/gratefultime-v2-backend
cp .env.example .env
nano .env
```

## 3. Install + systemd

```bash
chmod +x deploy/install.sh
./deploy/install.sh
```

This creates `~/.config/systemd/user/gratefultime-api.service` and starts it.

Useful commands:

```bash
systemctl --user status gratefultime-api
systemctl --user restart gratefultime-api
journalctl --user -u gratefultime-api -f
```

## 4. Caddy

Add the block from `deploy/Caddyfile.snippet` to your `~/Caddyfile` (or via Nest CLI if you manage domains that way):

```caddy
gratefultime-v2.eesa.hackclub.app {
	reverse_proxy 127.0.0.1:33540
}
```

Reload:

```bash
systemctl --user reload caddy
```

## 5. Verify

```bash
curl -s https://gratefultime-v2.eesa.hackclub.app/api/v1/
curl -s https://gratefultime-v2.eesa.hackclub.app/api/v1/commit
```

## 6. Mobile

```typescript
BaseUrl: "https://gratefultime-v2.eesa.hackclub.app"
UseLiveApi: true
```

## Deploy updates

```bash
ssh eesa.hackclub.app
cd ~/gratefultime-v2-backend
git pull
source .venv/bin/activate
pip install -r requirements.txt
systemctl --user restart gratefultime-api
```
