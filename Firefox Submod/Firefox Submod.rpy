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
    import store
    store.mas_submod_utils.submod_log.debug("Hey! Im starting!")
