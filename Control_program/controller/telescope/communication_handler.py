class TelescopeCommunication:
    def __init__(self, logger_, tconn_):
        self._logger = logger_
        self._tconn = tconn_

    def terminate(self):
        self._tconn.terminate()

    def set_LNA(self, turned_on):
        cmd = "SB8" if turned_on else "CB8"
        return self._tconn.send_and_receive(cmd) == ":"

    def set_noise_diode(self, turned_on):
        cmd = "SB9" if turned_on else "CB9"
        return self._tconn.send_and_receive(cmd) == ":"

    def reset_hardware(self):
        # Reset hardware to power-on (EEPROM) state
        return self._tconn.send_and_receive("RS") == "\r\n:"

    def reset_pointing(self):
        # Move telescope to end position to reset pointing
        self._tconn.send_and_receive("HX0")
        self._tconn.send_and_receive("HX1")
        self._tconn.send_and_receive("HX2")
        self._tconn.send_and_receive("HX3")
        return self._tconn.send_and_receive("XQ #INIT") == ":"

    def start_move_loop(self):
        # Deprecated and not needed as move loop is started in the #INIT
        # code in the new DMC program. For backwards-compatability.
        return

    def set_target_el_cog(self, new_al_cog):
        """
        Set the target altitude of the telescope.
        Argument in cognr.
        """
        maxel = self.get_maxel_cog()
        minel = self.get_minel_cog()
        if new_al_cog <= minel:
            new_al_cog = minel+1
        elif new_al_cog >= maxel:
            new_al_cog = maxel-1
        return self._tconn.send_and_receive("t_el=%d" % new_al_cog) == ":"

    def set_target_az_cog(self, new_az_cog):
        """
        Set the target azimuth of the telescope.
        Argument in cognr.
        """
        maxaz = self.get_maxaz_cog()
        minaz = self.get_minaz_cog()
        if new_az_cog <= minaz:
            new_az_cog = minaz+1
        elif new_az_cog >= maxaz:
            new_az_cog = maxaz-1
        return self._tconn.send_and_receive("t_az=%d" % new_az_cog) == ":"

    def get_know_pos(self):
        return self._get_int_from_telescope("knowpos") != 0

    def get_target_el_cog(self):
        """
        Return the target altitude cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("t_el")

    def get_target_az_cog(self):
        """
        Return the target azimuth cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("t_az")

    def get_current_el_cog(self):
        """
        Return the current altitude cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("c_el")

    def get_current_az_cog(self):
        """
        Return the current azimuth cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("c_az")

    def get_minel_cog(self):
        """
        Return the minimum altitude cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("minel")

    def get_maxel_cog(self):
        """
        Return the maximum altitude cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("maxel")

    def get_minaz_cog(self):
        """
        Return the minimum azimuth cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("minaz")

    def get_maxaz_cog(self):
        """
        Return the maximum azimuth cog number from the telescope
        as an integer.
        """
        return self._get_int_from_telescope("maxaz")

    def get_cog_step_az(self):
        return self._get_float_from_telescope("az_dpch")

    def get_cog_step_el(self):
        return self._get_float_from_telescope("el_dpch")

    def get_close_az(self):
        return self._get_int_from_telescope("vcls_az")

    def get_close_el(self):
        return self._get_int_from_telescope("vcls_el")

    def motors_running(self):
        """
        Returns true if telescope motors are on, false if motors are off.
        """
        d_az = int(abs(self.get_target_az_cog() - self.get_current_az_cog()))
        d_el = int(abs(self.get_target_el_cog() - self.get_current_el_cog()))
        return d_az > 0 or d_el > 0

    def stop_motors(self):
        # Max cogdistance for slow, pulsed motor movement
        self.set_target_az_cog(self.get_current_az_cog())
        self.set_target_el_cog(self.get_current_el_cog())

    def is_at_end_pos(self):
        return (self.get_current_el_cog() == self.get_minel_cog()
                and self.get_current_az_cog() == self.get_minaz_cog())

    def _data_from_response(self, response):
        """
        a response consists of
        """
        return response[1:-3]

    def _get_int_from_telescope(self, var_name):
        """
        Return the value of var_name stored in the telescope memory as an int.
        """
        return int(self._get_float_from_telescope(var_name))

    def _get_float_from_telescope(self, var_name):
        """
        Return the value of var_name in the telescope memory as a float.
        """
        return float(self._get_value_from_telescope(var_name))

    def _get_value_from_telescope(self, var_name):
        """
        Return the value of var_name in the telescope memory as a float.
        """
        response = self._tconn.send_and_receive("MG %s" % var_name)
        # response begins with ' ' and ends with '\r\n:'
        return response[:-1].strip()
