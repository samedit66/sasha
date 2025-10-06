from __future__ import annotations
from dataclasses import dataclass
import pexpect


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
    """
    Thin wrapper around pexpect.spawn to allow dialog-style interactions.

    Basic usage:
        shell = Terminal()  # defaults to bash -lc
        # If the command may prompt, provide expect_patterns to detect prompts:
        r = shell.send('sudo apt-get install package', expect_patterns=[r'[Pp]assword:'])
        if isinstance(r, Continue):
            shell.send('mysecretpassword')
        elif isinstance(r, Result):
            print('done:', r.output)
    """

    def __init__(
        self,
        shell_name: str = "bash",
        shell_args: str | list[str] = "-lc",
        env: dict[str, str] | None = None,
        encoding: str = "utf8",
        default_timeout: int = 30,
    ) -> None:
        self.shell_name = shell_name
        self.shell_args = [shell_args] if isinstance(shell_args, str) else shell_args
        self.env = env
        self.encoding = encoding
        self.default_timeout = default_timeout
        self.child: pexpect.spawn | None = None

    async def send(
        self,
        input_data: str,
        timeout: int | None = None,
        env: dict[str, str] | None = None,
        expect_patterns: list[str] | None = None,
    ) -> Response:
        """
        Send input_data to a shell process. If there is no existing child process,
        spawn one using `shell_name` + `shell_args + [input_data]`. Otherwise send
        the input to the existing child (using sendline).

        - expect_patterns: optional list of regular expressions. If any pattern matches,
          a Continue is returned (with matched text). EOF -> Result. TIMEOUT -> Timeout.
        """
        try:
            if timeout is None:
                timeout = self.default_timeout

            if env is None:
                env = self.env

            # spawn if first call
            if self.child is None:
                args = self.shell_args + [input_data]
                self.child = pexpect.spawn(
                    self.shell_name,
                    args=args,
                    env=env,
                    encoding=self.encoding,
                    timeout=timeout,
                )
            else:
                # use sendline to simulate user pressing Enter
                self.child.sendline(input_data)

            patterns = []
            if expect_patterns is not None:
                patterns.extend(expect_patterns)
            patterns.extend([pexpect.TIMEOUT, pexpect.EOF])

            index = await self.child.expect(patterns, timeout=timeout, async_=True)

            # pexpect.EOF
            if index == len(patterns) - 1:
                self.child.close(force=True)
                exit_status = self.child.exitstatus
                signal_status = self.child.signalstatus
                output = self.output()
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
        return (self.child.before or "").strip()

    def is_alive(self) -> bool:
        return self.child is not None and self.child.isalive()

    def close(self) -> None:
        if self.child is not None:
            self.child.close(force=True)
