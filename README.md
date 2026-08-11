# NCINS-200 — тесты метода расчёта страховой премии

Python-набор проверок для метода:

`POST /v1/ins-premium/calculate`

Источник требований: PDF-задача `[#NCINS-200] [НИБ] Метод расчета страховой премии.pdf`  
(Confluence-ссылки из задачи недоступны извне, поэтому контракт собран из примера запроса и headers в комментарии).

## Эндпоинт (test)

```
POST http://corp-gateway-test.moscow.alfaintra.net/corp-ncins-acc-gateway/secure/corp-ncins-acc-corp-ncins-acc-api/v1/ins-premium/calculate
```

Пример тела:

```json
{
  "programId": 3,
  "duration": 12,
  "insuranceSum": 500000.00,
  "insuranceObjects": [
    {
      "employeeFIO": "Сидоров Иван Сергеевич",
      "employeeBirthDate": "1995-05-20",
      "employeeEmail": "sidorov@example.com",
      "employeePhoneNumber": "+79991112233"
    }
  ]
}
```

Обязательные headers:

| Key | Value (пример) |
|---|---|
| A-userId | 123456 |
| A-customerId | 123456 |
| A-clientType | XXXXX |
| A-channelId | XXXXX |
| A-userIp | XXXXX |
| A-projectId | XXXXX |

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# при необходимости поправьте значения headers / BASE_URL в .env
```

## Запуск

Основной способ:

```bash
python app.py
```

Скрипт:
1. прогоняет проверки;
2. собирает ZIP с HTML/JUnit отчётом;
3. поднимает локальный сервер и печатает **ссылку на скачивание**.

Полезные опции:

```bash
python app.py --unit
python app.py --integration
python app.py --port 0            # случайный свободный порт (по умолчанию)
python app.py --port 8080         # фиксированный порт
python app.py --no-serve          # только отчёт, без HTTP-сервера
```

После запуска порт выбирается случайно; точная ссылка печатается в консоль, например:

```
http://127.0.0.1:<random-port>/reports/ncins200_test_results_latest.zip
http://127.0.0.1:<random-port>/reports/index.html
```

Альтернативно через pytest:

```bash
pytest -m unit
pytest
pytest -m integration
FORCE_INTEGRATION=1 pytest -m integration
```

## Что покрыто

- **unit**: валидация модели запроса, headers, client, разбор премии из ответа
- **integration / smoke**: happy-path из NCINS-200, несколько застрахованных, разные сроки/суммы
- **validation**: отсутствующие/невалидные поля, даты, email, phone, programId
- **headers**: отсутствие обязательных `A-*`, неверный Content-Type, неверные HTTP-методы
- **negative**: большие значения, XSS/SQL-подобные строки, дубликаты объектов
