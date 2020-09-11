from pyramid.config import Configurator

from sqlalchemy import engine_from_config

from .models import DBSession, Base

def main(global_config, **settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings,
                          root_factory='main_app.models.Root')
    config.include('pyramid_chameleon')
    config.add_route('home', '/')
    config.add_route('new_sale', '/new_sale')
    config.add_route('error_already_exists', '/error_already_exists')
    config.add_route('error_doesnt_exist', '/error_doesnt_exist')
    config.add_route('products', '/products')
    config.add_route('sale', '/sale/{uid}')
    config.add_route('delete', '/delete')
    config.add_static_view('deform_static', 'deform:static/')
    config.scan('.views')
    return config.make_wsgi_app()
