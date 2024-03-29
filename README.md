# Foodgram

![Workflow](https://github.com/kubanez-create/foodgram-project-react/actions/workflows/main.yml/badge.svg)

[**Посетить проект**](http://84.252.142.4/recipes).


Приложение для фуд-блоггеров, на текущий момент позволяет зарегистрированным пользователям:

- Добавлять собственные рецепты на платформу и редактировать их.
- Подписаться и отписаться на понравившегося блоггера.
- Просматривать рецепты авторов, на которых подписан
- Добавлять рецепты в избранные.
- Просматривать избранные рецепты.
- Добавлять рецепты в список покупок.
- Просматривать рецепты, отобранные для покупки.
- Скачивать список продуктов, необходимых для приготовления рецептов, отобранных для покупки.


## Стек технологий
- Python
- Django
- Django REST Framework
- PostgreSQL
- Docker

## Зависимости
- Перечислены в файле backend/requirements.txt

## Для запуска на собственном сервере

1. Установите на сервере `docker` и `docker compose`;
2. Создайте файл `/infra/.env`;
Внесите в данный файл переменные окружения:
```bash
SECRET_KEY=<Ваш_секретный_ключ>
DB_ENGINE=<база_данных>
DB_NAME=<произвольное_имя_базы_данных>
POSTGRES_USER=<имя_пользователя_базы_данных>
POSTGRES_PASSWORD=<пароль_к_базе_данных>
DB_HOST=<хост_базы_данных>
DB_PORT=<порт_базы_данных>
```
3. Из директории `/infra/` выполните команду `docker compose up -d --build`;
4. Выполните миграции `docker compose exec -it backend python manage.py migrate`;
5. Создайте Администратора `docker compose exec -it backend python manage.py createsuperuser`;
6. Соберите статику `docker compose exec backend python manage.py collectstatic --no-input`;
7. Из директории `/backend/foodgram/` загрузите фикстуры в Базу 
`sudo docker exec -it backend python manage.py loadcsv ingredients.csv.`

## Автор

- [Костенко Станислав](https://github.com/kubanez-create) 
