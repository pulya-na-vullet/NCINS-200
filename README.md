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

Для обхода `403 RBAC: access denied` клиент сам берёт токен Keycloak UMP
(`client_credentials`, client_id=`nib-corp-ncins`) по профилю `ENV=test|qa|dev`.

```bash
# .env
ENV=test
FETCH_KEYCLOAK_TOKEN=1
```

Если после токена всё ещё 403 — у клиента в Keycloak нет права на
`/v1/ins-premium/calculate` (в UMP часто выданы только `POST /applications`).
