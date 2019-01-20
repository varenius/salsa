class AbstractSatellite:
    def __init__(self, name, position_model_):
        self._name = name
        self._position_model = position_model_
        self._pos = self.compute_az_el()

    def name(self):
        return self._name

    def position(self):
        """
        Returns cached (az, el) as an AzEl
        """
        return self._pos

    def compute_az_el(self):
        """
        Refreshes the (az, el) values and returns them as an AzEl
        """
        self._pos = self._position_model.compute_az_el()
        return self.position()

    def copy(self, name, position_model_):
        raise NotImplementedError("Abstract Method")

    def __str__(self):
        return "%s @ %s" % (str(self._name), str(self._pos))



class ReferenceSatellite(AbstractSatellite):
    def __init__(self, GNSSname, position_model_):
        AbstractSatellite.__init__(self, GNSSname, position_model_)

    def copy(self, name, position_model_):
        return ReferenceSatellite(name, position_model_)


class CelestialObject(AbstractSatellite):
    def __init__(self, name, constellation, position_model_):
        AbstractSatellite.__init__(self, name, position_model_)
        self._constellation = constellation

    def get_constellation(self):
        return self._constellation

    def copy(self, name, position_model_):
        return CelestialObject(name, self._constellation, position_model_)
