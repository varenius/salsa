class TelescopePosInterface:
    """
    Interface between telescope cogs and corresponding positions.
    """
    def __init__(self, tcom_, min_az_, min_el_):
        self._tcom = tcom_

        self._min_el_cog = self._tcom.get_minel_cog()
        self._max_el_cog = self._tcom.get_maxel_cog()
        self._min_az_cog = self._tcom.get_minaz_cog()
        self._max_az_cog = self._tcom.get_maxaz_cog()
        self._n_steps_el = self._max_el_cog - self._min_el_cog
        self._n_steps_az = self._max_az_cog - self._min_az_cog

        # Smallest step separation in degrees, i.e. half cog-cog distance.
        self._cog_step_el = self._tcom.get_cog_step_el()
        self._cog_step_az = self._tcom.get_cog_step_az()

        self._min_az = min_az_
        self._max_az = self._min_az + self._n_steps_az*self._cog_step_az
        self._min_el = min_el_
        self._max_el = self._min_el + self._n_steps_el*self._cog_step_el

    def get_min_el(self):
        return self._min_el

    def get_min_az(self):
        return self._min_az

    def get_max_el(self):
        return self._max_el

    def get_max_az(self):
        return self._max_az

    def get_min_az_error(self):
        return self._cog_step_az

    def get_min_el_error(self):
        return self._cog_step_el

    def get_current_el(self):
        """
        Return the current altitude in degrees.
        """
        return self._min_el + self._cog_step_el*self._tcom.get_current_el_cog()

    def get_current_az(self):
        """
        Return the current azimuth in degrees.
        """
        return self._min_az + self._cog_step_az*self._tcom.get_current_az_cog()

    def get_target_el(self):
        """
        Return the target altitude in degrees.
        """
        return self._min_el + self._cog_step_el*self._tcom.get_target_el_cog()

    def get_target_az(self):
        """
        Return the target azimuth in degrees.
        """
        return self._min_az + self._cog_step_az*self._tcom.get_target_az_cog()

    def set_target_el(self, el):
        """
        Set the target altitude of the telescope.
        Argument in degrees.
        """
        new_el_cog = int(round((el - self._min_el) / self._cog_step_el))
        self._tcom.set_target_el_cog(new_el_cog)

    def set_target_az(self, az):
        """
        Set the target azimuth of the telescope.
        Argument in range 0 to 360 degrees relative to NORTH.
        """
        # Check if azimuth needs to be translated to local
        # range. Local range can be negative to less than 360 deg but still
        # cover a whole 360 degrees.
        if az > self._max_az:
            az -= 360.0
        new_az_cog = int(round((az - self._min_az) / self._cog_step_az))
        self._tcom.set_target_az_cog(new_az_cog)
