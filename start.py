#!/usr/bin/env python3.8
import asyncio
import functools
import importlib.util
import logging
import os
import signal
import sys

import hjson
from aiohttp import web
from telethon import functions, client

from common.transfer_helper import ParallelTransferrer

cfg_file_path = os.path.join(os.path.dirname(__file__), 'env.json')
cfg_obj = hjson.load(open(cfg_file_path))

debug = cfg_obj.get('debug', '0') != '0'

bot_list = []
web_runner = []

logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

log = logging.getLogger('telegram-background-bot')
logging.getLogger('telethon').setLevel(50)
logging.getLogger('urllib3').setLevel(50)
logging.getLogger('aiohttp.access').setLevel(50)

loop = asyncio.get_event_loop()
pg_name = 'telegram_bot_collection'


def json_error(status_code: int, exception: Exception) -> web.Response:
    """
    Returns a Response from an exception.
    Used for error middleware.
    :param status_code:
    :param exception:
    :return:
    """
    return web.Response(
        status=status_code,
        body=hjson.dumpsJSON({
            'error': exception.__class__.__name__,
            'detail': str(exception)
        }).encode('utf-8'),
        content_type='application/json')


async def error_middleware(app: web.Application, handler):
    """
    This middleware handles with exceptions received from views or previous middleware.
    :param app:
    :param handler:
    :return:
    """

    async def middleware_handler(request):
        try:
            response = await handler(request)
            if response.status == 404:
                return json_error(response.status, Exception(response.message))
            return response
        except web.HTTPException as ex:
            if ex.status == 404:
                return json_error(ex.status, ex)
            raise
        except Exception as e:
            return json_error(500, e)

    return middleware_handler


async def init_bot(tg_bot_client: client, token: str, trans: ParallelTransferrer) -> None:
    await tg_bot_client.start(bot_token=token)
    log.info(f'tb_bot started,{token.split(":")[0]}')
    dc_config = await tg_bot_client(functions.help.GetConfigRequest())
    for option in dc_config.dc_options:
        if option.ip_address == tg_bot_client.session.server_address:
            tg_bot_client.session.set_dc(option.id, option.ip_address, option.port)
            tg_bot_client.session.save()
            log.debug(f"Fixed DC ID in session from {tg_bot_client.session.dc_id} to {option.id}")
            break
    trans.post_init()
    pass


async def start_site(app: web.Application, route_object_in_web_module, address='localhost', port=8080):
    app.add_routes(route_object_in_web_module)
    runner = web.AppRunner(app)
    web_runner.append(runner)
    await runner.setup()
    site = web.TCPSite(runner, address, port)
    log.info(f'start site at {address}:{port}')
    await site.start()


async def start() -> None:
    all_bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
    all_web_dir = os.path.join(os.path.dirname(__file__), 'web')
    for fl in os.listdir(all_bot_dir):
        if fl.endswith('bot.py'):
            full = os.path.join(all_bot_dir, fl)

            bot_spec = importlib.util.spec_from_file_location('', full)
            bot_module = importlib.util.module_from_spec(bot_spec)
            bot_spec.loader.exec_module(bot_module)

            tg_client = getattr(bot_module, 'client')
            token = getattr(bot_module, 'bot_token')
            trans = getattr(bot_module, 'transfer')

            bot_list.append(tg_client)
            await init_bot(tg_client, token, trans)

            web_server = getattr(bot_module, 'web', None)
            if web_server is not None:
                web_name = web_server.get('name')
                port = web_server.get('port')
                host = web_server.get('host','127.0.0.1')
                if web_name is not None:
                    full_web = os.path.join(all_web_dir, web_name)
                    web_spec = importlib.util.spec_from_file_location('', full_web)
                    web_module = importlib.util.module_from_spec(web_spec)
                    web_spec.loader.exec_module(web_module)

                    route_obj = getattr(web_module, 'route')
                    bot_client = getattr(web_module, 'client')
                    try:
                        await bot_client.connect()
                    except:
                        pass

                    loop.create_task(
                        start_site(web.Application(middlewares=[error_middleware]), route_obj, host, port))


def disconnect_client():
    global bot_list
    for c in bot_list:
        print('dis-connect')
        c.disconnect()
    bot_list = []


def signal_handler(name):
    if os.path.isfile(f'{pg_name}.pid'):
        os.remove(f'{pg_name}.pid')
    print('signal_handler({!r})'.format(name))
    disconnect_client()
    sys.exit(0)


try:
    pid = os.getpid()
    with open(f'{pg_name}.pid', 'w') as f:
        f.write(str(pid))
    try:
        loop.add_signal_handler(
            signal.SIGTERM,
            functools.partial(signal_handler, name='SIGTERM'),
        )
    except NotImplementedError:
        pass

    try:
        loop.create_task(start())
        loop.run_forever()
    except KeyboardInterrupt:
        if os.path.isfile(f'{pg_name}.pid'):
            os.remove(f'{pg_name}.pid')
        print('\r\n')
        disconnect_client()
        sys.exit(0)
except Exception as ep:
    if os.path.isfile(f'{pg_name}.pid'):
        os.remove(f'{pg_name}.pid')
    disconnect_client()
    sys.exit(666)
