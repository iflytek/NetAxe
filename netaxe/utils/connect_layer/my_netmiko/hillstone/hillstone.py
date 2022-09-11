import re
import time

from netmiko import log
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_exception import (
    NetmikoAuthenticationException,
    ConfigInvalidException,
)


class HillstoneBase(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        # self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"#")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 511")
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    # 山石设备提示符 "#"
    def set_base_prompt(self, pri_prompt_terminator=r'#',
                        alt_prompt_terminator=r'#',
                        delay_factor=0.1):
        return super().set_base_prompt(pri_prompt_terminator=pri_prompt_terminator,
                                       alt_prompt_terminator=alt_prompt_terminator,
                                       delay_factor=delay_factor)

    def check_enable_mode(self, *args, **kwargs):
        """Hillstone has no enable mode."""
        pass

    def enable(self, *args, **kwargs):
        """Hillstone has no enable mode."""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """Hillstone has no enable mode."""
        return ""

    # config模式 (config)#
    def check_config_mode(self, check_string="(config)#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="configure", pattern="#", re_flags=0):
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config="exit", pattern=r"#"):
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, cmd="save", confirm=True, confirm_response="y"):
        """Save Config for HillstoneSSH，need confirm twice"""
        cmd = self.normalize_cmd(cmd)
        loop_delay = 0.2
        time.sleep(loop_delay)
        self.clear_buffer()
        self.write_channel(cmd)

        output = self.read_until_prompt_or_pattern(pattern=re.escape(r'[y]/n:'), )
        # confirm first
        self.write_channel(confirm_response)
        output += self.read_until_prompt_or_pattern(pattern=re.escape(r'y/[n]:'), )
        # hillstone need confirm twice
        self.write_channel(confirm_response)
        output += self.read_until_prompt_or_pattern(pattern=re.escape(r"#"), )
        output = self.normalize_linefeeds(output)

        return output

    def send_config_set(
            self,
            config_commands=None,
            exit_config_mode=True,
            delay_factor=1,
            max_loops=150,
            strip_prompt=False,
            strip_command=False,
            config_mode_command="configure",
            cmd_verify=True,
            enter_config_mode=True,
            error_pattern="",
    ):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.

        :param config_commands: Multiple configuration commands to be sent to the device
        :type config_commands: list or string

        :param exit_config_mode: Determines whether or not to exit config mode after complete
        :type exit_config_mode: bool

        :param delay_factor: Factor to adjust delays
        :type delay_factor: int

        :param max_loops: Controls wait time in conjunction with delay_factor (default: 150)
        :type max_loops: int

        :param strip_prompt: Determines whether or not to strip the prompt
        :type strip_prompt: bool

        :param strip_command: Determines whether or not to strip the command
        :type strip_command: bool

        :param config_mode_command: The command to enter into config mode
        :type config_mode_command: str

        :param cmd_verify: Whether or not to verify command echo for each command in config_set
        :type cmd_verify: bool

        :param enter_config_mode: Do you enter config mode before sending config commands
        :type exit_config_mode: bool

        :param error_pattern: Regular expression pattern to detect config errors in the
        output.
        :type error_pattern: str
        """
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ""
        elif isinstance(config_commands, str):
            config_commands = (config_commands,)

        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = ""
        if enter_config_mode:
            cfg_mode_args = (config_mode_command,) if config_mode_command else tuple()
            output += self.config_mode(*cfg_mode_args)

        # If error_pattern is perform output gathering line by line and not fast_cli mode.
        if self.fast_cli and self._legacy_mode and not error_pattern:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
            # Gather output
            output += self._read_channel_timing(
                delay_factor=delay_factor, max_loops=max_loops
            )

        elif not cmd_verify:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
                time.sleep(delay_factor * 0.05)

                # Gather the output incrementally due to error_pattern requirements
                if error_pattern:
                    output += self._read_channel_timing(
                        delay_factor=delay_factor, max_loops=max_loops
                    )
                    if re.search(error_pattern, output, flags=re.M):
                        msg = f"Invalid input detected at command: {cmd}"
                        raise ConfigInvalidException(msg)

            # Standard output gathering (no error_pattern)
            if not error_pattern:
                output += self._read_channel_timing(
                    delay_factor=delay_factor, max_loops=max_loops
                )

        else:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))

                # Make sure command is echoed
                new_output = self.read_until_pattern(pattern=re.escape(cmd.strip()))
                output += new_output

                # We might capture next prompt in the original read
                pattern = f"(?:{re.escape(self.base_prompt)}|#)"
                if not re.search(pattern, new_output):
                    # Make sure trailing prompt comes back (after command)
                    # NX-OS has fast-buffering problem where it immediately echoes command
                    # Even though the device hasn't caught up with processing command.
                    new_output = self.read_until_pattern(pattern=pattern)
                    output += new_output

                if error_pattern:
                    if re.search(error_pattern, output, flags=re.M):
                        msg = f"Invalid input detected at command: {cmd}"
                        raise ConfigInvalidException(msg)

        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        log.debug(f"{output}")
        return output

class HillstoneSSH(HillstoneBase):
    pass


class HillstoneTelnet(HillstoneBase):

    def telnet_login(
            self,
            pri_prompt_terminator=r"#\s*$",
            alt_prompt_terminator=r">\s*$",
            username_pattern=r"(?:user:|username|login|user name)",
            pwd_pattern=r"assword",
            delay_factor=1,
            max_loops=20,
    ):
        """Telnet login. Can be username/password or just password.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt
        :type pri_prompt_terminator: str

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt
        :type alt_prompt_terminator: str

        :param username_pattern: Pattern used to identify the username prompt
        :type username_pattern: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        :param max_loops: Controls the wait time in conjunction with the delay_factor
        (default: 20)
        """
        # print("telnet login start")
        delay_factor = self.select_delay_factor(delay_factor)

        # FIX: Cleanup in future versions of Netmiko
        if delay_factor < 1:
            if not self._legacy_mode and self.fast_cli:
                delay_factor = 1

        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output, flags=re.I):
                    # Sometimes username/password must be terminated with "\r" and not "\r\n"
                    self.write_channel(self.username + "\r")
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output, flags=re.I):
                    # Sometimes username/password must be terminated with "\r" and not "\r\n"
                    self.write_channel(self.password + "\r")
                    time.sleep(0.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if re.search(
                            pri_prompt_terminator, output, flags=re.M
                    ) or re.search(alt_prompt_terminator, output, flags=re.M):
                        return return_msg

                # Check if proper data received
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                        alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                self.write_channel(self.TELNET_RETURN)
                time.sleep(0.5 * delay_factor)
                i += 1
            except EOFError:
                self.remote_conn.close()
                msg = f"Login failed: {self.host}"
                raise NetmikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        msg = f"Login failed: {self.host}"
        self.remote_conn.close()
        raise NetmikoAuthenticationException(msg)

    pass
