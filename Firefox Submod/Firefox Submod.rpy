#=========auto submod update

# Register the submod
init -990 python:
    store.mas_submod_utils.Submod(
        author="SouceCalve",
        name="Firefox Submod",
        description="Adds a reaction to links in a Firefox! For work install a plugin from there: link",
        version="0.0.1",
    )

# Register the updater
init -989 python:
    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod="Firefox Submod",
            user_name="SouceCalve",
            repository_name="Test",
            #extraction_depth=1
        )


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

init 5 python:
    import store
    store.mas_submod_utils.submod_log.debug("Hey! Im starting!")

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


