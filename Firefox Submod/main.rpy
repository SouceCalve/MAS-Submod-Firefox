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
        "web.telegram.org":"fs_telegram"
    }

# Функции обработки
init 0 python:
    import store
    @mas_submod_utils.functionplugin("ch30_loop")
    def check_domain_queue():
        """
        Main processing function (hooked to ch30_loop)
        Continuosly checking domains and add Events
        """
        try:
            # Securely checking queue without blocking
            if not domain_queue.empty():
                domain = domain_queue.get_nowait()

                # Domain logging disabled right now, but you can still enable it to debug queue
                # store.mas_submod_utils.submod_log.debug(f"Proccesing domain: {domain}")

                # If domain found found on list, when add a Event to MAS queue
                if domain in domain_to_event:
                    event_label = domain_to_event[domain]
                    MASEventList.queue(event_label)
                    store.mas_submod_utils.submod_log.debug("Event " +  str(event_label) + " appended in MAS queue")

        except Queue.Empty:
            # If our queue is empty - doing nothing
            pass
        except Exception as e:
            # Logging error, but continue to work
            store.mas_submod_utils.submod_log.error("Error in check_domain_queue:" + str(e))







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
                # Receiving a request
                data = self.request.recv(4096)

                # Raw data logging disabled, but still can enable it if you want to debug Plugin-->Server exchange
                #store.mas_submod_utils.submod_log.debug("Got a raw data: " + repr(data) + "\r\n")

                # Parsing a HTTP request
                if data:
                    # Covertiong to a string
                    request_text = data

                    # Logging a string request
                    #store.mas_submod_utils.submod_log.debug("Got request:\n" + request_text + "\r\n")

                    # Parsing a first string
                    lines = request_text.split('\r\n')
                    if lines:
                        first_line = lines[0]
                        #store.mas_submod_utils.submod_log.debug("First string of request: " + first_line + "\r\n")

                        # Checking if it a POST request on /domain
                        if 'POST' in first_line and '/domain' in first_line:
                            # Finding a body in request (after a clear string)
                            body_start = request_text.find('\r\n\r\n')
                            if body_start != -1:
                                body = request_text[body_start + 4:]
                                #store.mas_submod_utils.submod_log.debug("Body of request: " + body + "\r\n")

                                try:
                                    # Parsing JSON
                                    data_json = json.loads(body)
                                    domain = data_json.get('domain', '')
                                    store.mas_submod_utils.submod_log.debug("Extracted domain: " + domain + "\r\n")
                                    if not(store.persistent.domain_now == domain):
                                        store.persistent.domain_now = domain

                                    # Forming a HTTP answer with CORS headers
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
                                    store.mas_submod_utils.submod_log.debug("CORS-compilent answer sended right away.\r\n")
                                    domain_queue.put(domain)
                                except ValueError as e:
                                    store.mas_submod_utils.submod_log.error("Error parsing JSON structure: " + str(e) + "\r\n")
                                    self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                            else:
                                store.mas_submod_utils.submod_log.error("Body not found!\r\n")
                                self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                        elif 'OPTIONS' in first_line and '/domain' in first_line:
                            # Proccesing preflight OPTIONS request for CORS
                            store.mas_submod_utils.submod_log.debug("Got a OPTIONS preflight request\r\n")
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
                            store.mas_submod_utils.submod_log.debug("Unknown request detected: " + first_line + "\r\n")
                            self.request.sendall("HTTP/1.1 404 Not Found\r\n\r\n")
                    else:
                        self.request.sendall("HTTP/1.1 400 Bad Request\r\n\r\n")
                else:
                    store.mas_submod_utils.submod_log.debug("Empty body\r\n")

            except Exception as e:
                store.mas_submod_utils.submod_log.error("General error in parser: " + str(e) + "\r\n")

    def start_server():
        """Function for starting server in another thread"""
        try:
            # Using ThreadingTCPServer for processing multiple connections
            api_server = SocketServer.ThreadingTCPServer(("", PORT), MyRequestHandler)

            # Allowing multiple uses of same address
            api_server.allow_reuse_address = True

            store.mas_submod_utils.submod_log.debug("Server started on port: " + str(PORT) + "\r\n")

            # Starting server
            api_server.serve_forever()
        except Exception as e:
            store.mas_submod_utils.submod_log.error("General server error: " + str(e) + "\r\n")
        finally:
            store.mas_submod_utils.submod_log.debug("Server stopped.\r\n")

    # Creating and staring a server thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # Daemon mode (should shutdown gracefully with main thread, as i know)
    server_thread.start()

    # another log string, to check if the thread has started at all
    #store.mas_submod_utils.submod_log.debug("Looks like a server thread start\r\n")

init 5 python:

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
