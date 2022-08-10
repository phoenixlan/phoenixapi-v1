import logging
log = logging.getLogger(__name__)

def includeme(config):
    settings = config.get_settings()
    log.info(settings)
    
    config.add_static_view('static', './static', cache_max_age=3600)
    config.add_static_view('files', settings['files.static_view_root'], cache_max_age=3600)

    #config.add_subscriber(verify_token_event, NewRequest)
    

    # Pages
    config.add_route('home', '/')
    
    # Oauth
    config.add_route('login', '/oauth/auth')
    config.add_route('oauth_token', '/oauth/token')
    config.add_route('oauth_validate', '/oauth/client/validate')
