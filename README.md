# Marketplaces_FBS_order_packing

Скрипт для сборки "в один клик" заказов отгрузки СЕГОДНЯШНЕГО дня, печати стикеров, листов сборки и актов для отгрузки на маркетплейсах по схеме работы FBS.

Скрипты необходимо запускать строго в календарный день отгрузки! Файл для каждого маркетплейса запускается отдельно.

В настоящее время добавлены маркетплейсы OZON, Wildberries, Yandex Market

Для начала работы необходимо ввести данные аккаутов маркетплейсов, указанные в файле .env_example и переименовать файл в .env
Все ключи должны быть добавлены в формате string. Если какой-то маркетплейс не используется, то необходимо оставить строчку .env в исходном состоянии.

На выходе должны быть получены .pdf файлы для отгрузки формата:
"<Текущая дата> <Название маркетплейса> <Название магазина> <Labels/Assemble list/Act>.pdf"


