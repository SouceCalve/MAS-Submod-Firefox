init 6 python:
    import store
    import SocketServer
    import threading
    import json

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
                                    process_domain(domain)
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

    def process_domain(domain):
        """Обрабатывает полученный домен и запускает соответствующие ивенты"""
        # Маппинг доменов на WRS ивенты
        domain_to_event = {
            "github.com": "mas_wrs_github",
            "youtube.com": "mas_wrs_youtube",
            "twitter.com": "mas_wrs_twitter",
            "reddit.com": "mas_wrs_reddit",
            "pinterest.com": "mas_wrs_pinterest",
            # Добавьте другие домены
        }

        if domain in domain_to_event:
            eventlabel = domain_to_event[domain]
            # Проверяем, можно ли запустить ивент
            ev = mas_getEV(eventlabel)
            if ev and ev.checkConditional():
                MASEventList.queue(eventlabel)
                store.mas_submod_utils.submod_log.debug("Запущен ивент: " + str(eventlabel) + " для домена: " + str(domain) + "\r\n")
                return True
        return False

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
            eventlabel="wrs_github",
            category=["github.com"],
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

label wrs_github:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Looking at code, [player]?",
            "Working on a project?",
            "Found something interesting on GitHub?"
        ],
        'Window Reactions'
    )

    if not wrs_success:
        $ mas_unlockFailedWRS('wrs_github')
    return

