# YT Minimal — CLAUDE.md

## Visão geral
App mobile minimalista sobre o YouTube. Remove Shorts, exibe feed só como texto
(título, canal, duração). Reprodução padrão é vídeo; modo apenas áudio é opcional
e ativado por toggle explícito do usuário.

## Stack
- Backend: Python 3.11+, FastAPI, httpx, python-dotenv,
  python-jose[cryptography], cryptography, slowapi
- Mobile: React Native com Expo SDK 51+, TypeScript, expo-secure-store,
  expo-web-browser, expo-av

## Autenticação
- Fluxo: OAuth 2.0 Google (YouTube scope), via expo-web-browser no app
- Backend recebe callback, troca code por tokens, armazena refresh_token
  criptografado com Fernet, retorna JWT de sessão (1h de expiração)
- App armazena JWT em expo-secure-store; renova automaticamente via /auth/refresh
- Scopes necessários:
    https://www.googleapis.com/auth/youtube.readonly

## Regras de negócio críticas
1. NUNCA exibir vídeos com duração < 3 minutos
2. NUNCA exibir thumbnails — UI é 100% texto
3. Reprodução padrão: vídeo via YouTube player embed ou expo-av
4. Modo áudio: REMOVIDO — player simplificado para "Ver no YouTube" via expo-web-browser
5. O toggle de modo áudio deve persistir na sessão (não entre sessões)
6. Recomendações vêm do feed personalizado do usuário autenticado
   (endpoint: activities, subscriptions, videos)

## Segurança — obrigatório
- Todos os endpoints exceto /auth/login e /auth/callback exigem JWT válido
- Rate limiting: 60 req/min por IP, 200 req/min por user_id
- Rate limiting extra nos endpoints de auth: 30/min em /auth/login, 10/min em /auth/callback
- CORS: apenas origem explícita do app (configurável via ENV)
- Refresh tokens: sempre criptografados com Fernet antes de salvar
- Inputs: validação Pydantic em todos os endpoints, extra="forbid"
- Logs: NUNCA logar tokens, access_tokens, refresh_tokens ou PII
- Headers HTTP de segurança: X-Content-Type-Options, X-Frame-Options,
  Strict-Transport-Security (via middleware/security.py)

## Infraestrutura atual
- GitHub: repositório privado em https://github.com/araujocostamkt/yt-minimal
- Backend: hospedado no Render.com em https://yt-minimal.onrender.com
  - Python fixado na versão 3.11.9 via .python-version na raiz do repo
  - Deploy automático a partir do branch master
- Mobile: desenvolvimento local via Expo Go
  - EXPO_PUBLIC_API_BASE_URL=https://yt-minimal.onrender.com (em mobile/.env)

## Variáveis de ambiente obrigatórias
### Backend (configurar no painel do Render)
YOUTUBE_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://yt-minimal.onrender.com/auth/callback
JWT_SECRET_KEY=          # gerar com: openssl rand -hex 32
FERNET_KEY=              # gerar com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ALLOWED_ORIGINS=         # ex: ytminimal://,exp://...
PYTHON_VERSION=3.11.9    # redundância para garantir versão no Render

### Mobile (mobile/.env — nunca commitar)
EXPO_PUBLIC_API_BASE_URL=https://yt-minimal.onrender.com

## Comandos úteis
- Backend: `uvicorn main:app --reload` (pasta backend/)
- Mobile: `npx expo start --clear` (pasta mobile/ — sempre usar --clear ao depurar)
- Audit: `pip-audit` (backend/)

## Fixes aplicados (histórico técnico)

### Backend
- `requirements.txt`: yt-dlp despinado (estava fixo em versão ~16 meses antiga)
- `routers/auth.py`: rate limiting adicionado em /auth/login (30/min) e /auth/callback (10/min)
- `services/auth_service.py`: grace period de 24h para refresh de JWT (evita logout abrupto)
- `services/auth_service.py`: adicionado `openid` ao scope OAuth — sem ele Google não retorna
  `id_token`, causando KeyError silencioso em `exchange_code()` → todo login falhava com
  `error=internal` mesmo sem nenhuma mensagem de erro visível
- `services/feed_service.py`: substituído `playlist_ids[:15]` (truncava silenciosamente) por
  asyncio.Semaphore(15) — busca todos os canais com concorrência limitada
- `token_store.py`: migrado de dict em memória para SQLite via `sqlite3` built-in
- `routers/auth.py`: adicionado rate limit de 30/min em `/auth/refresh` (gap de segurança)

### Mobile
- `app.json`: adicionado plugin `expo-router` (ausência causava tela branca)
- `app.json`: removido `expo-secure-store` dos plugins (crashava o Expo Go)
- `app/_layout.tsx`: trocado `<Slot>` por `<Stack>` (Slot não inicializa o stack de navegação)
- `app/_layout.tsx`: removido código de SplashScreen (expo-splash-screen não estava instalado,
  o import no nível do módulo causava crash antes do React iniciar — não capturável por ErrorBoundary)
- `app/_layout.tsx`: adicionado export `ErrorBoundary` customizado (mostra erro real na tela)
- `app/index.tsx`: substituído `<Redirect>` durante render por `router.replace()` em useEffect
  (Redirect durante render bloqueia a inicialização do Stack)
- `app/player.tsx`: adicionado botão "Ver no YouTube" via expo-web-browser quando não há stream direto
- `src/hooks/useAuth.ts`: verifica expiração do JWT salvo antes de marcar como autenticado;
  faz refresh silencioso se expirado
- `src/components/VideoPlayer.tsx`: adicionado prop `onError`
- `tsconfig.json`: adicionado `"moduleResolution": "bundler"` (corrige aviso de depreciação do TS)
- `src/components/AudioPlayer.tsx`, `ModeToggle.tsx`, `VideoPlayer.tsx`: removidos — modo áudio eliminado; player simplificado para "Ver no YouTube" via expo-web-browser
- `routers/audio.py`, `services/audio_service.py`: removidos — yt-dlp e modo áudio eliminados do backend

## Pendências
1. Registrar `https://yt-minimal.onrender.com/auth/callback` no Google Cloud Console
   (Authorized redirect URIs) para o OAuth funcionar em produção
2. Confirmar que todos os env vars abaixo estão configurados no painel do Render:
   YOUTUBE_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
   JWT_SECRET_KEY, FERNET_KEY, ALLOWED_ORIGINS
3. ALLOWED_ORIGINS deve incluir o scheme do app: `ytminimal://` e se testar via Expo Go,
   também o endereço `exp://...` mostrado pelo `expo start`
4. Verificar se o crash "Something went wrong" no Expo Go foi resolvido após o commit fa0bed1
   (remoção do SplashScreen). Rodar: `npx expo start --clear`
5. Testar fluxo completo após 1–4: login → feed → player

## Limitação conhecida (token_store.py)
O `token_store.py` usa SQLite (`tokens.db`). No Render free tier, o filesystem é
efêmero — o arquivo é perdido em cada restart/hibernate (~15 min de inatividade),
e os usuários precisam fazer login novamente. Aceitável para MVP; futuramente
substituir por Redis ou banco de dados persistente (configurar `TOKEN_DB_PATH`
para um volume montado, quando disponível).

## Convenções
- Backend: snake_case, type hints obrigatórios, Pydantic com extra="forbid"
- Mobile: componentes funcionais, TypeScript estrito, sem libs de UI externas
- Nunca commitar .env; usar .env.example com valores fictícios
- Sempre rodar `expo start --clear` ao depurar problemas de bundle no Expo Go