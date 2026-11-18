# Autenticação JWT — HomeCore Cloud

## Login

`POST /api/v1/auth/login/`

```json
{"username": "alice", "password": "sua-senha"}
```

Resposta HTTP 200:

```json
{"access": "<access-jwt>", "refresh": "<refresh-jwt>"}
```

Use o access token em endpoints protegidos:

```http
Authorization: Bearer <access-jwt>
```

- `POST /api/v1/auth/refresh/` com `{"refresh": "<refresh-jwt>"}` para renovar o access token.
- `POST /api/v1/auth/verify/` com `{"token": "<access-jwt>"}` para verificar um token.

## Swagger

Abra http://localhost:8000/api/docs/, use o endpoint de login e copie o `access`. Clique em **Authorize**, selecione o esquema Bearer JWT e cole o token (sem incluir `Bearer `, quando o campo já indicar o esquema). Teste `GET /api/v1/tenants/`.

## Segurança e limitações

- Login inicial é por **username**, não por email.
- Access token: 15 minutos. Refresh token: 1 dia.
- Sessões Django continuam funcionando para o Admin e clientes web.
- Use HTTPS fora do localhost. Nunca registre senhas ou tokens em logs.
- O refresh token ainda não possui rotação nem revogação server-side. Logout, revogação, rate limiting e OIDC serão implementados antes de disponibilizar autenticação na internet.
- Não use a chave secreta de desenvolvimento em produção.
- Criar um tenant via `POST /api/v1/tenants/` concede papel owner ao usuário autenticado.
- Este recurso não altera o banco e não exige migrations.

## Verificação

```bash
docker compose up --build -d
docker compose exec api python manage.py check
docker compose exec api pytest -q
```
