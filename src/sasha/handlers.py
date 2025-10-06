import re

import aiogram
from aiogram import types, enums
from aiogram.filters import command

from sasha.core import shell


router = aiogram.Router()


@router.message(command.Command("check", "health", "check_health"))
async def check_health(message: types.Message) -> None:
    await message.reply("Alive!")


@router.message(command.Command("exec", "execute"))
async def execute(
    message: types.Message,
    command: command.CommandObject,
    terminal: shell.Command,
) -> None:
    if command.args is None:
        await message.reply("❗ Expected a command to execute")
        return

    shell_command = command.args
    result = await terminal.send(shell_command)
    await message.reply(text=output_message(result))


def output_message(shell_response: shell.Response, max_len: int = 3500) -> str:
    """
    Format a shell.Response into a Markdown message string.

    - Uses fenced code blocks for command output / errors to avoid needing to escape
      Markdown special characters.
    - Chooses a fence made of backticks longer than any backtick-run inside the content,
      so embedded backticks won't break the block.
    - Truncates very long outputs.
    """

    def _truncate(s: str | None, max_len: int = 3500) -> str:
        if s is None:
            return "<no output>"
        s = str(s)
        if len(s) > max_len:
            return s[: max_len - 1] + "…(truncated)"
        return s

    def _fence_wrap(s: str | None) -> str:
        """Wrap `s` in a backtick fence that's longer than any run of backticks in `s`."""
        s = _truncate(s)
        # find longest sequence of backticks in the content
        runs = re.findall(r"`+", s)
        max_run = max((len(r) for r in runs), default=0)
        fence = "`" * max(3, max_run + 1)  # at least triple-backtick
        # ensure there's no trailing spaces after fence line
        return f"{fence}\n{s}\n{fence}"

    match shell_response:
        case shell.Error(error=error, output=output):
            ...

    # Error (fatal/unrecoverable)
    if isinstance(shell_response, shell.Error):
        err_block = _fence_wrap(getattr(shell_response, "error", "<no error message>"))
        partial_block = _fence_wrap(getattr(shell_response, "output", None))
        header = "❌ **Error talking to process**"
        return (
            f"{header}\n\n**Error:**\n{err_block}\n\n"
            f"**Partial output (if any):**\n{partial_block}\n\n"
            "The session was terminated. 🔴"
        )

    # Result (command finished)
    if isinstance(shell_response, shell.Result):
        output_block = _fence_wrap(shell_response.output)
        exit_status = shell_response.exit_status
        signal_status = shell_response.signal_status
        header = f"🟢 **Result** — exit={exit_status} signal={signal_status}"
        return f"{header}\n\n{output_block}"

    # Continue (interactive prompt / matched pattern)
    if isinstance(shell_response, shell.Continue):
        output_block = _fence_wrap(shell_response.output)
        matched_block = _fence_wrap(getattr(shell_response, "matched", "<no matched text>"))
        header = "🟡 **Interactive / Prompt detected**"
        return (
            f"{header}\n\n{output_block}\n\n"
            f"**Matched prompt:**\n{matched_block}\n\n"
            "The process is waiting for more input — send the next piece of input to continue. ⏳"
        )

    # Timeout (partial output delivered, process still alive)
    if isinstance(shell_response, shell.Timeout):
        output_block = _fence_wrap(shell_response.output)
        timeout_val = getattr(shell_response, "timeout", "unknown")
        header = f"⏱️ **Timeout** — partial output (waited {timeout_val} sec)"
        return (
            f"{header}\n\n{output_block}\n\n"
            "The command timed out but the process may still be alive. You can send more input to continue the session. 🟠"
        )

    # Fallback for unknown / unexpected variants
    return f"⚪️ Unexpected shell response:\n{_fence_wrap(repr(shell_response))}"
