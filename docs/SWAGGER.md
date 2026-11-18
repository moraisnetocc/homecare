# Documentação interativa — HomeCore Cloud

Após iniciar os containers, abra:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI schema: http://localhost:8000/api/schema/

## Autenticação nos testes

Os endpoints de gestão da API exigem autenticação. Nesta fase, a autenticação disponível é a sessão Django (não existe endpoint de login JWT/OIDC ainda).

1. Crie um superusuário com `docker compose exec api python manage.py createsuperuser`, caso ainda não exista.
2. Faça login em http://localhost:8000/admin/ no mesmo navegador.
3. Abra http://localhost:8000/api/docs/ e use **Try it out**.
4. Para POSTs, a proteção CSRF da sessão continua obrigatória. O navegador deve enviar cookie de sessão e token CSRF; se receber 403 CSRF, teste o POST com um cliente que envie ambos ou aguarde a implementação da autenticação por token.

**Atenção:** o superusuário Django não tem acesso automático aos tenants pela API. Crie um tenant por `POST /api/v1/tenants/` para receber o papel `owner`.

## Verificação

```bash
docker compose up --build -d
docker compose exec api python manage.py check
docker compose exec api python manage.py spectacular --validate --fail-on-warn
docker compose exec api pytest -q
```

Não são necessárias migrations. A interface Swagger UI carrega seus recursos visuais de CDN; para ambientes offline, avaliaremos drf-spectacular-sidecar. Antes de expor documentação em produção, restringir acesso e revisar configurações de segurança.
