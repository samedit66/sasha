import re

import aiogram
from aiogram import types
from aiogram.enums import parse_mode
from aiogram.filters import command

from src.sasha.core import terminal


router = aiogram.Router()


@router.message(command.Command("check", "health", "check_health"))
async def check_health(message: types.Message) -> None:
    await message.reply("Alive!")


@router.message(command.Command("exec", "execute"))
async def execute(
    message: types.Message,
    command: command.CommandObject,
    term: terminal.Terminal,
) -> None:
    if command.args is None:
        await message.reply("❗ Expected a command to execute")
        return

    shell_command = command.args
    result = await term.send(shell_command)
    await message.reply(
        text=output_message(result), parse_mode=parse_mode.ParseMode.MARKDOWN_V2
    )


def output_message(shell_response: terminal.Response, max_len: int = 3500) -> str:
    """
    Format a shell.Response into a Markdown message string.

    - Uses fenced code blocks for command output / errors to avoid needing to escape
      Markdown special characters.
    - Chooses a fence made of backticks longer than any backtick-run inside the content,
      so embedded backticks won't break the block.
    - Truncates very long outputs.
    """
    match shell_response:
        case terminal.Error(error=error, output=output):
            return (
                "🔴 **Error talking to process**\n\n"
                f"**Error:**\n{prepare_output_data(error, max_len)}\n\n"
                f"**Partial output (if any):**\n{prepare_output_data(output, max_len)}\n\n"
                "The session was terminated."
            )

        case terminal.Result(
            output=output, exit_status=exit_status, signal_status=signal_status
        ):
            return (
                f"🟢 **Result** — exit={exit_status} signal={signal_status}\n\n"
                f"{prepare_output_data(output, max_len)}"
            )

        case terminal.Continue(output=output, matched=matched):
            return (
                "🟡 **Interactive / Prompt detected**\n\n"
                f"{prepare_output_data(output, max_len)}\n\n"
                f"**Matched prompt:**\n{prepare_output_data(matched, max_len)}\n\n"
                "The process is waiting for more input — send the next piece of input to continue. ⏳"
            )

        case terminal.Timeout(output=output, timeout=timeout):
            return (
                f"⏱️ **Timeout** — partial output (waited {timeout} sec)\n\n"
                f"{prepare_output_data(output, max_len)}\n\n"
                "The command timed out but the process may still be alive. You can send more input to continue the session. 🟠"
            )

        case _:
            # Fallback for unknown / unexpected variants
            return f"⚪️ Unexpected shell response:\n{prepare_output_data(repr(shell_response), max_len)}"


def prepare_output_data(output_data: str | None, max_len: int) -> str:
    """
    Wrap `output_data` in a fenced code block suitable for Markdown and truncate if too long.
    If output_data is None, return a simple placeholder.
    """
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
