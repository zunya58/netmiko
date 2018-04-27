from __future__ import print_function
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoTimeoutException


class HPComwareSSH(CiscoSSHConnection):

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        i = 1
        while i <= 4:
            # Comware can have a banner that prompts you to continue
            # 'Press Y or ENTER to continue, N to exit.'
            time.sleep(.5 * delay_factor)
            self.write_channel("\n")
            i += 1

        time.sleep(.3 * delay_factor)
        self.clear_buffer()
        self._test_channel_read(pattern=r'[>\]]')
        self.set_base_prompt()
        command = self.RETURN + "screen-length disable"
        self.disable_paging(command=command)
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command='system-view'):
        """Enter configuration mode."""
        return super(HPComwareSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='return'):
        """Exit config mode."""
        return super(HPComwareSSH, self).exit_config_mode(exit_config=exit_config)

    def check_config_mode(self, check_string=']'):
        """Check whether device is in configuration mode. Return a boolean."""
        return super(HPComwareSSH, self).check_config_mode(check_string=check_string)

    def set_base_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']',
                        delay_factor=1):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """
        prompt = super(HPComwareSSH, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

        # Strip off leading character
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(self, cmd='super level-15', pattern=r'ssword', re_flags=re.IGNORECASE):
        """Escalate privileges."""
        delay_factor = self.select_delay_factor(1)
        output = ""
        msg = "Failed to enter privilege-level 15. Please ensure you pass " \
              "the 'secret' argument to ConnectHandler."
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            i = 1
            max_loops = 6
            while i <= max_loops:
                new_data = self.read_channel()
                try:
                    # Comware in certain contexts will prompt for a username
                    if re.search(r'Username', new_data, flags=re.I):
                        self.write_channel(self.username + self.RETURN)
                        time.sleep(1 * delay_factor)
                        output += new_data
                        new_data = self.read_channel()
                    # Search for password pattern / send password
                    if re.search(pattern, new_data, flags=re.I):
                        self.write_channel(self.secret + self.RETURN)
                        time.sleep(1 * delay_factor)
                        output += new_data
                        new_data = self.read_channel()
                    if 'Password has not been set' in new_data:
                        raise ValueError(msg)
                    if re.search(r'\<.+\>', new_data):
                        output += new_data
                        break
                    i += 1

                except NetMikoTimeoutException:
                    raise ValueError(msg)

            # FIX - Need a way to validate that we actually went into priv 15
            # if not self.check_enable_mode():
            #     raise ValueError(msg)
        return output

    def exit_enable_mode(self, exit_command=''):
        """No exit of enable mode implemted on Comware."""
        return ""

    def check_enable_mode(self, check_string=''):
        return False

    def save_config(self, cmd='save force', confirm=False):
        """Save Config."""
        return super(HPComwareSSH, self).save_config(cmd=cmd, confirm=confirm)
