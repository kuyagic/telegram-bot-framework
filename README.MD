### Telegram Bot 整合工具

#### 系统配置要求

1. Python 3.6+

#### 使用方法
- Clone Repo
- 复制 `env.sample.json` → `env.json`
- bot 文件夹下的为 Bot 处理程序,对应 `env.json` 的key. 定义 `token` 和是否使用代理, 默认代理在 每个bot的py 文件里自行定义.
- web 下为对应bot的web处理程序,不是必须项目.
- 修改 config 下对应的配置文件.
- `python3 start.py` 启动


#### 添加 bot 流程
- 在 `bot` 文件夹下 新建 一个 以 `bot.py` 结尾的 文件, 例如 `test_bot.py`
- 在 `env.json` 中添加 如下 节点和 内容
```json
"test_bot.py" : {"token":"","use_proxy":"1"}
```
如果需要 web 接口 则
```json
"test_bot.py": {
    "token": "",
    "use_proxy": "1",
    "web":{
        "name": "test_bot_web.py",
        "port": 12345
    }
},
"test_bot_web.py": {
    "bot": "test_bot.py"
}

```
- 如果有 对应 web接口 则需要按照 `env.sample.json` 下 添加 对应 的 `web` 节点配置,指定 web的 py处理文件名,并新建web.py对应的 bot 文件名.
