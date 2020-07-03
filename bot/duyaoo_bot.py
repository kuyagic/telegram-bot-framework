import logging
import os

import hjson
from telethon import TelegramClient, events

from common.transfer_helper import ParallelTransferrer

log = logging.getLogger(os.path.basename(__file__))

# region Config
session_file = os.path.join('session', os.path.basename(__file__))
session_key = os.path.basename(__file__)
log.debug(f'session={session_file}')

bot_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', session_key + '.json')
# print(__file__, 'config', bot_config_file)

env_config_file = os.path.join(os.path.dirname(__file__), '..', 'env.json')
# print('env', env_config_file)

bot_config = hjson.load(open(bot_config_file))
env_config = hjson.load(open(env_config_file))

api_id = env_config.get('tg_api_id')
api_hash = env_config.get('tg_api_hash')
bot_token = env_config.get(session_key).get('token')
use_proxy = env_config.get(session_key).get('use_proxy', '0') != '0'
web = env_config.get(session_key).get('web')
# endregion

log.info(f'{os.path.basename(__file__)},Initialization complete')
log.info(f'Proxy={use_proxy}')
log.debug(f'BotToken={bot_token}')

if use_proxy:
    import socks

    proxy = (socks.SOCKS5, '127.0.0.1', 1789)
    client = TelegramClient(session_file, api_id, api_hash, proxy=proxy)
else:
    client = TelegramClient(session_file, api_id, api_hash)

transfer = ParallelTransferrer(client)


@client.on(events.NewMessage(pattern='/start'))
async def handle_start(evt: events.NewMessage.Event) -> None:
    await evt.reply(os.path.basename(__file__))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern='/id'))
async def handel_link(evt: events.NewMessage.Event) -> None:
    await evt.reply(str(evt.input_chat.user_id))
    raise events.StopPropagation
    pass
