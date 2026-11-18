# Sprint 003 — Ambientes e dispositivos

## Endpoints

- `GET/POST /api/v1/rooms/`; `GET/PATCH/PUT/DELETE /api/v1/rooms/{id}/`
- `GET/POST /api/v1/devices/`; `GET/PATCH/PUT/DELETE /api/v1/devices/{id}/`
- As listas aceitam `?home=<uuid>` para filtrar por casa.
- Swagger: `/api/docs/`

## Catálogo global reutilizável

- `GET/POST /api/v1/device-types/` e `GET/PATCH/PUT/DELETE /api/v1/device-types/{id}/`
- `GET/POST /api/v1/device-models/` e `GET/PATCH/PUT/DELETE /api/v1/device-models/{id}/`
- Qualquer usuário autenticado pode consultar o catálogo; apenas usuários `is_staff` podem criar, editar ou excluir tipos/modelos.
- `DeviceModel`: `device_type`, `manufacturer`, `model`, `protocol`, `capabilities` e `image` opcional.
- Upload de `image` via `multipart/form-data` (PNG/JPEG/WebP etc. validados por Pillow; limite 5 MB). A resposta inclui `image_url` absoluta ou `null`.
- A URL `GET /api/v1/device-models/{id}/image/` serve a imagem publicamente para permitir exibição em clientes sem headers Bearer; **não envie imagens privadas** ao catálogo.
- Imagens são persistidas no volume Docker `media_data`. Para produção, usar object storage/CDN e política de tamanho, quota, rate limit e limpeza de arquivos substituídos.
- `Device.device_model` é FK opcional; equipamentos legados continuam válidos. `Device.kind` e `Device.capabilities` permanecem dados da instância e não são sincronizados automaticamente com o catálogo.
- Não é possível excluir um modelo ainda associado a dispositivos (`PROTECT`).

## Exemplo de dispositivo

```json
{
  "home": "<uuid-da-casa>",
  "room": "<uuid-do-ambiente>",
  "device_model": "<uuid-do-modelo>",
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
