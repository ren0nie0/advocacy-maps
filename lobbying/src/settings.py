import logging

save_type = 'psql'

params_dict = {
    'host'      : 'localhost',
    'port'      : '5432',
    'database'  : 'maple_lobbying',
    'user'      : 'geekc',
    'password'  : 'asdf'
}

logging.basicConfig(level=logging.DEBUG)
