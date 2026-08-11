# NCINS-200 — тесты метода расчёта страховой премии

Метод: `POST /v1/ins-premium/calculate`  
Чек-лист: [`CHECKLIST.md`](CHECKLIST.md)

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Что делает `python app.py`:
- гоняет API-проверки через **requests + pytest**;
- пишет нормальный лог в консоль (запрос/ответ/статус каждого теста);
- сохраняет текстовый отчёт `reports/report.txt` = чек-лист + результаты;
- **веб-сервер не поднимает**.

Опции:

```bash
python app.py              # API-тесты метода (по умолчанию)
python app.py --unit       # только unit без сети
python app.py --all        # unit + api
python app.py -v           # подробный лог
python app.py --skip-if-offline   # skip API, если gateway недоступен
```

Нужен доступ к test-gateway (корп VPN).

Токен берётся **как в Postman-коллекции** `Insurance API Tests`:

```
POST {{tokenUrl}}
grant_type=client_credentials
client_id=nib-corp-ncinsurance-accounting
client_secret=nib_corp_ncinsurance_accounting
```

TEST `tokenUrl`:
`http://corp-gateway-test.../mks-gateway/public/auth/realms/corporate/protocol/openid-connect/token`

Issuer в JWT: `http://keycloak-nib-int/realms/corporate`  
(не UMP `idp-api-test.../realms/ump` — из‑за него был `Jwt issuer is not configured`).

```bash
# .env
ENV=test
FETCH_KEYCLOAK_TOKEN=1
```

Коллекция лежит в `postman/`.
