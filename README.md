# Тесты POST /v1/sign/create-operation

Метод:

```
POST /corp-ncins-gateway/secure/corp-ncins-corp-ncins-api/v1/sign/create-operation
```

Чек-лист: [`CHECKLIST.md`](CHECKLIST.md)

## Запуск

```bash
pip install -r requirements.txt
python app.py
```

Что делает `python app.py`:
- сам делает `cp .env.example .env` (если `.env` нет) и прописывает UMP TEST credentials;
- гоняет API-проверки через **requests + pytest**;
- пишет лог в консоль (запрос/ответ/статус);
- сохраняет текстовый отчёт `reports/report.txt`;
- собирает ZIP архив проекта в `dist/` (и в `/opt/cursor/artifacts/`) — его можно приложить к задаче.

Опции:

```bash
python app.py              # API-тесты + ZIP
python app.py --unit       # только unit без сети
python app.py --all        # unit + api
python app.py --zip-only   # только архив
python app.py -v           # подробный лог
python app.py --skip-if-offline
```

Нужен доступ к test-gateway (корп VPN).

## Токен (Keycloak UMP, client `nib-corp-ncins`)

```
POST {{tokenUrl}}
grant_type=client_credentials
client_id=nib-corp-ncins
client_secret=<из профиля ENV>
```

| ENV | tokenUrl |
|---|---|
| test | `https://idp-api-test.alfaintra.net/auth/realms/ump/protocol/openid-connect/token` |
| qa | `https://keycloak.umpqak8sm1.moscow.alfaintra.net/realms/ump/protocol/openid-connect/token` |
| dev | `https://keycloak.umpdevwk8sm1.moscow.alfaintra.net/realms/ump/protocol/openid-connect/token` |

SSL для token/API по умолчанию `verify=0` (как `curl -k`).

## Пример запроса

```bash
curl --request POST \
  --url https://corp-gateway-test.moscow.alfaintra.net/corp-ncins-gateway/secure/corp-ncins-corp-ncins-api/v1/sign/create-operation \
  --header 'A-channelId: nib' \
  --header 'A-clientType: MOBILE' \
  --header 'A-customerId: 123456' \
  --header 'A-projectId: corp-ncinsurance' \
  --header 'A-userId: 123456' \
  --header 'Authorization: Bearer ...' \
  --header 'Content-Type: application/json' \
  --data '{
  "userId": "XAGA56",
  "clientId": "UAY4DP",
  "documentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}'
```

Postman: `postman/create-operation.collection.json` + environment `test`/`dev`.
