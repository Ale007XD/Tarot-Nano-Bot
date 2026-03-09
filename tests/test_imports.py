def run():

    import bot.main
    import bot.database
    import bot.config

    import bot.services.tarot_engine
    import bot.services.llm_service

    import bot.handlers.start
    import bot.handlers.tarot
    import bot.handlers.payment
    import bot.handlers.referral
