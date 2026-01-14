# Общие данные
init -1 python:
    import Queue
    domain_queue = Queue.Queue()
    domain_to_event = {
        "github.com": "mas_wrs_monikamoddev", #Adding mostly all sites reaction from MAS code
        "wikipedia.org": "mas_wrs_wikipedia",
        "duolingo.com":"mas_wrs_duolingo",
        "youtube.com":"mas_wrs_youtube",
        "rule34.xxx":"mas_wrs_r34m",
        "rule34.us":"mas_wrs_r34m",
        "rule34.paheal.net":"mas_wrs_r34m",
        "x.com":"mas_wrs_twitter",
        "4chan.org":"mas_wrs_4chan",
        "pixiv.net":"mas_wrs_pixiv",
        "reddit.com":"mas_wrs_reddit",
        "myanimelist.net":"mas_wrs_mal",
        "deviantart.com":"mas_wrs_deviantart",
        "netflix.com":"mas_wrs_netflix",
        "twitch.tv":"mas_wrs_twitch",
        "crunchyroll.com":"mas_wrs_crunchyroll",
        "pinterest.com":"mas_wrs_pinterest",
        "web.telegram.org":"fs_telegram",         #Also adding some russian-specific reaction too ;)
        "ru.wikipedia.org":"fs_ru_wikipedia",
        "ru.pinterest.com":"fs_ru_penterest"
    }

# Функции обработки
init 0 python:
    import store
    @mas_submod_utils.functionplugin("ch30_loop")
    def check_domain_queue():
        """
        Функция, вызываемая из главного потока (хука ch30_loop)
        Проверяет очередь доменов и запускает соответствующие события
        """
        try:
            # Безопасно проверяем очередь без блокировки
            if not domain_queue.empty():
                domain = domain_queue.get_nowait()

                # Включаем логирование для отладки
                # store.mas_submod_utils.submod_log.debug(f"Обрабатываем домен из очереди: {domain}")

                # Если домен есть в списке, ставим событие в очередь MAS
                if domain in domain_to_event:
                    event_label = domain_to_event[domain]
                    MASEventList.queue(event_label)
                    store.mas_submod_utils.submod_log.debug("Событие " +  str(event_label) + " поставлено в очередь MAS")

        except Queue.Empty:
            # Очередь пуста - ничего не делаем
            pass
        except Exception as e:
            # Логируем ошибку, но не прерываем работу
            store.mas_submod_utils.submod_log.error("Ошибка в check_domain_queue:" + str(e))







init 6 python:
    import store
    import SocketServer
    import threading
    import json
    import Queue

    PORT = 9163


    class MyRequestHandler(SocketServer.BaseRequestHandler):
        def handle(self):
            try:
                # Получаем данные
                data = self.request.recv(4096)

                # Логируем сырые данные
                #store.mas_submod_utils.submod_log.debug("Получены сырые данные: " + repr(data) + "\r\n")

                # Парсим HTTP запрос
                if data:
                    # Преобразуем в строку для парсинга
                    request_text = data

                    # Логируем запрос
                    #store.mas_submod_utils.submod_log.debug("Получен запрос:\n" + request_text + "\r\n")

                    # Парсим первую строку
                    lines = request_text.split('\r\n')
                    if lines:
                        first_line = lines[0]
                        #store.mas_submod_utils.submod_log.debug("Первая строка запроса: " + first_line + "\r\n")

                        # Проверяем, что это POST запрос на /domain
                        if 'POST' in first_line and '/domain' in first_line:
                            # Ищем тело запроса (после пустой строки)
                            body_start = request_text.find('\r\n\r\n')
                            if body_start != -1:
                                body = request_text[body_start + 4:]
                                #store.mas_submod_utils.submod_log.debug("Тело запроса: " + body + "\r\n")

                                try:
                                    # Парсим JSON
                                    data_json = json.loads(body)
                                    domain = data_json.get('domain', '')
                                    store.mas_submod_utils.submod_log.debug("Извлечен домен: " + domain + "\r\n")
                                    if not(store.persistent.domain_now == domain):
                                        store.persistent.domain_now = domain

                                    # Формируем HTTP ответ с CORS заголовками
                                    response_data = json.dumps({"status": "ok", "domain": domain})
                                    response = (
                                        "HTTP/1.1 200 OK\r\n"
                                        "Content-Type: application/json\r\n"
                                        "Access-Control-Allow-Origin: *\r\n"
                                        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                                        "Access-Control-Allow-Headers: Content-Type\r\n"
                                        "Content-Length: {}\r\n"
                                        "\r\n"
                                        "{}"
                                    ).format(len(response_data), response_data)

                                    self.request.sendall(response)
                                    store.mas_submod_utils.submod_log.debug("Отправлен ответ с CORS заголовками\r\n")
                                    domain_queue.put(domain)
                                except ValueError as e:
                                    store.mas_submod_utils.submod_log.error("Ошибка парсинга JSON: " + str(e) + "\r\n")
                                    self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                            else:
                                store.mas_submod_utils.submod_log.error("Не найдено тело запроса\r\n")
                                self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                        elif 'OPTIONS' in first_line and '/domain' in first_line:
                            # Обрабатываем preflight OPTIONS запрос для CORS
                            store.mas_submod_utils.submod_log.debug("Получен OPTIONS preflight запрос\r\n")
                            response = (
                                "HTTP/1.1 200 OK\r\n"
                                "Access-Control-Allow-Origin: *\r\n"
                                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                                "Access-Control-Allow-Headers: Content-Type\r\n"
                                "Content-Length: 0\r\n"
                                "\r\n"
                            )
                            self.request.sendall(response)
                        else:
                            store.mas_submod_utils.submod_log.debug("Неизвестный запрос: " + first_line + "\r\n")
                            self.request.sendall("HTTP/1.1 404 Not Found\r\n\r\n")
                    else:
                        self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                else:
                    store.mas_submod_utils.submod_log.debug("Получены пустые данные\r\n")

            except Exception as e:
                store.mas_submod_utils.submod_log.error("Ошибка в обработчике: " + str(e) + "\r\n")

    def start_server():
        """Функция для запуска сервера в отдельном потоке"""
        try:
            # Используем ThreadingTCPServer для обработки множественных подключений
            api_server = SocketServer.ThreadingTCPServer(("", PORT), MyRequestHandler)

            # Разрешаем повторное использование адреса
            api_server.allow_reuse_address = True

            store.mas_submod_utils.submod_log.debug("Сервер запущен на порту: " + str(PORT) + "\r\n")

            # Запускаем сервер
            api_server.serve_forever()
        except Exception as e:
            store.mas_submod_utils.submod_log.error("Ошибка сервера: " + str(e) + "\r\n")
        finally:
            store.mas_submod_utils.submod_log.debug("Сервер остановлен\r\n")

    # Создаем и запускаем поток с сервером
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # Демон-поток (завершится с основной программой)
    server_thread.start()

    # Для проверки что поток запустился
    store.mas_submod_utils.submod_log.debug("Сервер запущен в отдельном потоке\r\n")

init 5 python:
    # GitHub
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="fs_ru_wikipedia",
            category=["sites-reaction"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

    # GitHub
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="fs_ru_penterest",
            category=["sites-reaction"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )
    # GitHub
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="fs_telegram",
            category=["sites-reaction"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label fs_github:
    $ fs_success = mas_display_notif(
        m_name,
        [
            "Looking at code, [player]?",
            "Working on a project?",
            "Found something interesting on GitHub?"
        ],
        'Window Reactions'
    )

    if not fs_success:
        $ mas_unlockFailedWRS('fs_github')
    return

label fs_ru_wikipedia:
    $ wikipedia_reacts = [
        "Изучаешь что-то новое, [player]?",
        "Исследуешь тему понемножку, [player]?"
    ]

    #Items in here will get the wiki article you're looking at for reacts.
    python:
        wind_name = mas_getActiveWindowHandle()
        try:
            cutoff_index = wind_name.index(" - Wikipedia")

            #If we're still here, we didn't value error
            #Now we get the article
            wiki_article = wind_name[:cutoff_index]

            # May contain clarification in trailing parentheses
            wiki_article = re.sub("\\s*\\(.+\\)$", "", wiki_article)
            wikipedia_reacts.append(renpy.substitute("'[wiki_article]'...\nЗвучит интересно, [player]."))

        except ValueError:
            pass

    $ fs_success = mas_display_notif(
        m_name,
        wikipedia_reacts,
        'Window Reactions'
    )

    #Unlock again if we failed
    if not fs_success:
        $ mas_unlockFailedWRS('fs_ru_wikipedia')
    return

label fs_ru_penterest:
    $ fs_success = mas_display_notif(
        m_name,
        [
            "Что-то новенькое появилось, [player]?",
            "Я не знала, что тебя это заинтересует, [player]?",
            "Понравилось что-нибудь?"
        ],
        'Window Reactions'
    )



    if not fs_success:
        $ mas_unlockFailedWRS('fs_ru_penterest')
    return

label fs_telegram:
    $ fs_success = mas_display_notif(
        m_name,
        [
            "Oh? Gosh, you were on Telegram, [player]?",
            "Just make sure you save your most meaningful conversations for me, okay? Ehehe~",
            "Well, you know, keeping tabs on me through the Telegram, [player]? Ehehe, I'm a little flattered~"
        ],
        'Window Reactions'
    )



    if not fs_success:
        $ mas_unlockFailedWRS('fs_telegram')
    return
