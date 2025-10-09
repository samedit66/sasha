# sasha

> Execute remote commands via a Telegram bot.

`sasha` is a small Telegram bot that lets you run shell commands on a remote host via Telegram messages.  
It supports truly interactive terminal sessions, so interactive prompts (for example, a `sudo` password or a Python REPL) can be handled from the Telegram chat.

![Usage example image](https://github.com/samedit66/sasha/blob/main/media/usage_example.png?raw=true)

## Features

- Truly interactive sessions (supports interactive prompts such as `sudo` or an interactive Python shell).
- Simple configuration via environment variables / a `.env` file.
- Lightweight and easy to run on a home server, VPS, or inside a container.

## Usage

1. Ensure you have [`uv`](https://github.com/astral-sh/uv) installed.

2. Fill in the values in the `.env.example` file:
```bash
# Bot token. Obtain it from @BotFather.
TELEGRAM_BOT_TOKEN=
# User IDs that are allowed to use this bot instance.
# Be careful when specifying this.
# Separate multiple user IDs with commas.
TELEGRAM_USER_ID=

# Shell that will be executed.
SHELL_NAME="bash"
# Default arguments. Because the shell is interactive, we pass "-i" explicitly.
# When running on Windows, omit this - PowerShell runs in interactive mode by default.
SHELL_ARGS="-i"
# Timeout (in seconds). Some commands may run a long time and this may be an error.
# To prevent that, you can set a timeout for execution.
# When undefined, timeout is infinite.
SHELL_TIMEOUT=30
```

3. Run the following:

```bash
git clone https://github.com/samedit66/sasha.git
cd sasha
cp .env.example .env
uv run main.py
```

4. Check if the bot is alive by sending `/check` command
