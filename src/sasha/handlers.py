import re

import aiogram
from aiogram import types
from aiogram.enums import parse_mode
from aiogram.filters import command

from src.sasha.core import terminal

router = aiogram.Router()


@router.message(command.Command("check", "health", "check_health"))
async def check_health(message: types.Message) -> None:
    await message.reply("✅ Alive")


@router.message(aiogram.F.text)
async def execute(
    message: types.Message,
    term: terminal.InteractiveTerminal,
) -> None:
    shell_command = message.text.strip()
    result = await term.send(shell_command)
    await message.reply(
        text=output_message(result), parse_mode=parse_mode.ParseMode.MARKDOWN_V2
    )


def output_message(shell_response: terminal.Response, max_len: int = 3500) -> str:
    match shell_response:
        case terminal.Error(error=error, output=output):
            return (
                "🔴 **Process error**\n\n"
                f"**Error:**\n{prepare_output_data(error, max_len)}\n\n"
                f"**Partial output:**\n{prepare_output_data(output, max_len)}\n\n"
                "Session terminated\\."
            )

        case terminal.Result(
            output=output, exit_status=exit_status, signal_status=signal_status
        ):
            return (
                f"🟢 **Result:** exit\\={exit_status}, signal\\={signal_status}\n\n"
                f"{prepare_output_data(output, max_len)}"
            )

        case terminal.Continue(output=output, matched=matched):
            return (
                "🟡 **Interactive prompt detected**\n\n"
                f"{prepare_output_data(output, max_len) + "\n\n" if output else ""}"
                f"**Prompt:**\n{prepare_output_data(matched, max_len)}\n\n"
                "Process awaiting input \\- send the next input to continue\\. ⏳"
            )

        case terminal.Timeout(output=output, timeout=timeout):
            output_block = prepare_output_data(output, max_len) if output else "No output\\."
            return (
                f"⏱️ **Timeout** \(waited {timeout} sec\)\n\n"
                f"{output_block}\n\n"
                "Command timed out, but the process may still be running\\. You can send more input to continue\\."
            )

        case _:
            # Fallback for unknown / unexpected variants
            return f"⚪️ Unexpected shell response:\n{prepare_output_data(repr(shell_response), max_len)}"


def prepare_output_data(output_data: str | None, max_len: int) -> str:
    if output_data is None:
        return "<no output>"

    if len(output_data) > max_len:
        output_data = output_data[: max_len - 1] + "... (truncated)"

    # find longest sequence of backticks in the content
    runs = re.findall(r"`+", output_data)
    max_run = max((len(r) for r in runs), default=0)
    fence = "`" * max(3, max_run + 1)  # at least triple-backtick

    # ensure there's no trailing spaces after fence line
    return f"{fence}\n{output_data}\n{fence}"
