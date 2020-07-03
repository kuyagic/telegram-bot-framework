import importlib.util
import logging
import os

import hjson
from aiohttp import web

log = logging.getLogger(os.path.basename(__file__))
route = web.RouteTableDef()

# region Config
session_key = os.path.basename(__file__)
log.debug(f'session={session_key}')

web_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', session_key + '.json')
# print(__file__, 'config', bot_config_file)

env_config_file = os.path.join(os.path.dirname(__file__), '..', 'env.json')
# print('env', env_config_file)

web_config = hjson.load(open(web_config_file))
env_config = hjson.load(open(env_config_file))
# endregion

# import bot.py
log.info(f'{"#"*10} web {os.path.basename(__file__)} import begin {"#"*10}')
module_file = os.path.join(os.path.dirname(__file__), '..', 'bot', env_config.get(session_key).get('bot'))
spec = importlib.util.spec_from_file_location('', module_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
log.info(f'{"#"*10} web {os.path.basename(__file__)} import end {"#"*10}')
client = getattr(module, 'client')
transfer = getattr(module, 'transfer')
transfer.post_init()


@route.get(r'/')
async def index(req: web.Request) -> web.Response:
    try:
        if web_config.get('show_index', '0') != '0':
            self_me = await client.get_me()
            index_html = f'<a target="_blank" href="https://t.me/{self_me.username}">{self_me.first_name}</a><br/>'
            return web.Response(status=200, text=index_html, content_type='text/html')
        else:
            return web.Response(status=403, text='<h3>403 Forbidden</h3>', content_type='text/html')
    except Exception as ep:
        return web.Response(status=200, text=str(ep), content_type='text/html')
