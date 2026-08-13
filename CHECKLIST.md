# Проверки метода POST /v1/sign/create-operation

Метод:
`POST https://corp-gateway-test.moscow.alfaintra.net/corp-ncins-gateway/secure/corp-ncins-corp-ncins-api/v1/sign/create-operation`

Токен: тот же, что в Postman Insurance API Tests  
(`mks-gateway` / `realms/corporate`, `client_credentials`, `nib-corp-ncinsurance-accounting`)

| № | Проверка | Что именно проверяет |
|---|---|---|
| 1 | Happy-path из curl | Body `userId/clientId/documentId` + headers из curl → 200/201 и id операции |
| 2 | Валидные headers из curl | `A-channelId=nib`, `A-clientType=MOBILE`, `A-projectId=corp-ncinsurance` → 200/201 |
| 3 | Ответ JSON | Content-Type JSON и тело — объект |
| 4 | Повторный вызов | Второй запрос с тем же телом не даёт 5xx |
| 5 | Обязательный header A-userId | Без `A-userId` → 400/401/403/422 |
| 6 | Обязательный header A-customerId | Без `A-customerId` → ошибка |
| 7 | Обязательный header A-clientType | Без `A-clientType` → ошибка |
| 8 | Обязательный header A-channelId | Без `A-channelId` → ошибка |
| 9 | Обязательный header A-projectId | Без `A-projectId` → ошибка |
| 10 | Без Authorization | Запрос без Bearer → 401/403 |
| 11 | Метод только POST | GET на тот же URL → 404/405 |
| 12 | Content-Type | Неверный Content-Type → 400/415/422 |
| 13 | Нет userId | Отсутствие обязательного поля → 400/422 |
| 14 | Нет clientId | Отсутствие обязательного поля → 400/422 |
| 15 | Нет documentId | Отсутствие обязательного поля → 400/422 |
| 16–21 | Пустые/null поля | `""` / `null` для обязательных полей → 400/422 |
| 22 | documentId не UUID | Невалидный формат → 400/422 |
| 23 | Несуществующий documentId | UUID-заглушка → 400/404/422 |
| 24 | Пустое тело | `{}` → 400/422 |
| 25 | Лишнее поле | Либо 400/422, либо успех (игнор extra) |

Запуск: `python app.py`
