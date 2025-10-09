from __future__ import annotations

import re
from dataclasses import dataclass
import uuid

import pexpect
import coloredstrings as cs


@dataclass
class Result:
    """Command finished (EOF)."""

    output: str
    exit_status: int | None
    signal_status: int | None


@dataclass
class Continue:
    """Process is still running and waiting for more input (or matched an interactive prompt)."""

    output: str
    matched: str | None = None  # the matched pattern text


@dataclass
class Error:
    """A fatal error occurred while talking to the process."""

    error: str
    output: str | None = None


@dataclass
class Timeout:
    """A timeout happened; process is still alive and can be continued."""

    output: str
    timeout: int


type Response = Result | Continue | Error | Timeout


class Terminal:
    def __init__(
        self,
        shell_name: str = "bash",
        shell_args: str | list[str] = "-i",
        env: dict[str, str] | None = None,
        encoding: str = "utf8",
        default_timeout: int = 30,
        expect_patterns: list[str] | None = None,
        echo: bool = False,
    ) -> None:
        self.shell_name = shell_name
        self.shell_args = [shell_args] if isinstance(shell_args, str) else shell_args
        self.env = env
        self.encoding = encoding
        self.default_timeout = default_timeout
        self.expect_patterns = expect_patterns
        self.echo = echo
        self.child: pexpect.spawn | None = None
        self.prompt: str | None = None

    async def send(
        self,
        input_data: str,
        timeout: int | None = None,
        env: dict[str, str] | None = None,
        expect_patterns: list[str] | None = None,
    ) -> Response:
        try:
            if timeout is None:
                timeout = self.default_timeout

            if env is None:
                env = self.env

            if expect_patterns is None:
                expect_patterns = self.expect_patterns

            # spawn if first call
            if self.child is None:
                self.child = pexpect.spawn(
                    self.shell_name,
                    args=self.shell_args,
                    env=env,
                    encoding=self.encoding,
                    timeout=timeout,
                    echo=self.echo,
                )

                # Set a unique, stable prompt and disable PROMPT_COMMAND
                unique = f"PEXPECT_PROMPT_{uuid.uuid4().hex}> "

                if self.shell_name.endswith("powershell") or self.shell_name in ("pwsh", "powershell.exe"):
                    # PowerShell: clear window title and override prompt function
                    # Use single quotes so the string is literal and not interpolated.
                    self.child.sendline("$Host.UI.RawUI.WindowTitle = ''")
                    self.child.sendline(f"function prompt {{ '{unique}' }}")
                else:
                    # Bash-ish: disable PROMPT_COMMAND and set a fixed PS1
                    self.child.sendline("export PROMPT_COMMAND=''")
                    self.child.sendline(f"export PS1='{unique}'") 

                # Wait for our new prompt to appear, then store an escaped regex for it
                await self.child.expect(re.escape(unique), timeout=10, async_=True)
                self.prompt = re.escape(unique)

            # use sendline to simulate user pressing Enter
            self.child.sendline(input_data)

            patterns = [
                self.prompt,
                *expect_patterns.copy(),
                pexpect.TIMEOUT,
                pexpect.EOF,
            ]
            index = await self.child.expect(patterns, timeout=timeout, async_=True)

            # pexpect.EOF or prompt
            eof = index == len(patterns) - 1
            if eof or index == 0:
                if eof:
                    self.child.close(force=True)

                exit_status = self.child.exitstatus
                signal_status = self.child.signalstatus
                output = self.output()

                if eof:
                    self.child = None
                return Result(output, exit_status, signal_status)

            # pexpect.TIMEOUT
            if index == len(patterns) - 2:
                partial = self.output()
                return Timeout(output=partial, timeout=timeout)

            # We matched one of the expect_patterns
            matched_text = self.child.after
            return Continue(output=self.child.before, matched=matched_text)

        except Exception as exc:
            # Unrecoverable / unexpected error
            partial = None
            if self.child is not None:
                partial = self.output()
                self.child.close(force=True)
                self.child = None
            return Error(error=str(exc), output=partial)

    def output(self) -> str:
        return cs.strip_ansi(self.child.before or "").strip()

    def is_alive(self) -> bool:
        return self.child is not None and self.child.isalive()

    def close(self) -> None:
        if self.child is not None:
            self.child.close(force=True)
