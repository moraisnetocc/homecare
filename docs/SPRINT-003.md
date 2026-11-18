# Sprint 003 — Ambientes e dispositivos

## Endpoints

- `GET/POST /api/v1/rooms/`; `GET/PATCH/PUT/DELETE /api/v1/rooms/{id}/`
- `GET/POST /api/v1/devices/`; `GET/PATCH/PUT/DELETE /api/v1/devices/{id}/`
- As listas aceitam `?home=<uuid>` para filtrar por casa.
- Swagger: `/api/docs/`

## Exemplo de dispositivo

```json
{
  "home": "<uuid-da-casa>",
  "room": "<uuid-do-ambiente>",
  "name": "Lâmpada da sala",
  "kind": "light",
  "external_id": "ha:light.sala",
  "capabilities": ["on_off", "brightness"]
}
```

`room` é opcional. `kind` aceita `light`, `outlet`, `switch`, `sensor`, `thermostat` e `other`. `capabilities` é uma lista de identificadores de capacidade; não representa execução de comandos. `external_id` é opcional e único dentro de uma casa quando preenchido.

## Segurança e escopo

- Leitura: membros da casa e administradores/proprietários do tenant.
- Escrita: proprietário da casa ou administrador/proprietário do tenant.
- Recursos de outras casas não aparecem na listagem e retornam 404 no detalhe.
- `room` deve pertencer à mesma casa que o dispositivo.
- `state` e `is_available` são somente leitura nesta API: sincronização de estado real será implementada com o agente local e integração autenticada.
- Apagar um ambiente deixa os dispositivos sem ambiente; apagar uma casa elimina seus ambientes e dispositivos.
- Não há controle físico de dispositivos neste sprint; o modelo é independente de Home Assistant.

## Testes

```bash
docker compose up --build -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py makemigrations --check --dry-run
docker compose exec api pytest -q
```
