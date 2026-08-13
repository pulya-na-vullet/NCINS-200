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
- сам делает `cp .env.example .env` (если `.env` нет) и прописывает credentials `nib-corp-ncinsurance`;
- гоняет API-проверки через **requests + pytest**;
- пишет лог в консоль (запрос/ответ/статус);
- сохраняет текстовый отчёт `reports/report.txt`;
- собирает ZIP архив проекта в `dist/` — его можно приложить к задаче.

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

## Токен (НИБ, от бэкенда)

```bash
curl --location 'http://corp-gateway-test.moscow.alfaintra.net/mks-gateway/public/auth/realms/corporate/protocol/openid-connect/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'client_id=nib-corp-ncinsurance' \
  --data-urlencode 'client_secret=nib_corp_ncinsurance'
```

Не путать с:
- `nib-corp-ncinsurance-accounting` — accounting gateway
- `nib-corp-ncins` (UMP) — заявки `/applications`

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
