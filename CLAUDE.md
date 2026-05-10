# YT Minimal — CLAUDE.md

## Visão geral
App mobile minimalista sobre o YouTube. Remove Shorts, exibe feed só como texto
(título, canal, duração). Reprodução padrão é vídeo; modo apenas áudio é opcional
e ativado por toggle explícito do usuário.

## Stack
- Backend: Python 3.11+, FastAPI, yt-dlp, httpx, python-dotenv,
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
4. Modo áudio: ativado por toggle explícito; usa yt-dlp (bestaudio)
5. O toggle de modo áudio deve persistir na sessão (não entre sessões)
6. Recomendações vêm do feed personalizado do usuário autenticado
   (endpoint: activities, subscriptions, videos)

## Segurança — obrigatório
- Todos os endpoints exceto /auth/login e /auth/callback exigem JWT válido
- Rate limiting: 60 req/min por IP, 200 req/min por user_id
- CORS: apenas origem explícita do app (configurável via ENV)
- Refresh tokens: sempre criptografados com Fernet antes de salvar
- Inputs: validação Pydantic em todos os endpoints, extra="forbid"
- Logs: NUNCA logar tokens, access_tokens, refresh_tokens ou PII
- Headers HTTP de segurança: X-Content-Type-Options, X-Frame-Options,
  Strict-Transport-Security (via middleware/security.py)

## Variáveis de ambiente obrigatórias
YOUTUBE_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://seubackend.com/auth/callback
JWT_SECRET_KEY=          # gerar com: openssl rand -hex 32
FERNET_KEY=              # gerar com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ALLOWED_ORIGINS=         # ex: exp://192.168.x.x:8081,ytminimal://

## Comandos úteis
- Backend: `uvicorn main:app --reload` (pasta backend/)
- Mobile: `npx expo start` (pasta mobile/)
- Audit: `pip-audit` (backend/)

## Convenções
- Backend: snake_case, type hints obrigatórios, Pydantic com extra="forbid"
- Mobile: componentes funcionais, TypeScript estrito, sem libs de UI externas
- Nunca commitar .env; usar .env.example com valores fictícios