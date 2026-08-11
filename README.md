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

## Скачать весь проект

https://github.com/pulya-na-vullet/NCINS-200/archive/refs/heads/cursor/ncins-200-ins-premium-tests-0f4d.zip

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env
python app.py
```

`python app.py` упаковывает **весь проект** (с `app.py`) в ZIP и поднимает локальный сервер на случайном порту со ссылкой на скачивание.

```bash
python app.py --no-serve                 # только собрать ZIP проекта
python app.py --test --unit              # unit-тесты без VPN
python app.py --test --integration       # API-тесты, нужен корп VPN
python app.py --port 8080
```

Integration к `corp-gateway-test...` без корпоративного VPN не выполнится (skip).

## Что покрыто

- **unit**: валидация модели запроса, headers, client, разбор премии из ответа
- **integration / smoke**: happy-path из NCINS-200, несколько застрахованных, разные сроки/суммы
- **validation**: отсутствующие/невалидные поля, даты, email, phone, programId
- **headers**: отсутствие обязательных `A-*`, неверный Content-Type, неверные HTTP-методы
- **negative**: большие значения, XSS/SQL-подобные строки, дубликаты объектов
