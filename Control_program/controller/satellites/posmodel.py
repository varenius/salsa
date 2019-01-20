from numpy import cos, radians
from controller.util import AzEl


class PositionModel:
    def __init__(self, f_compute_az_el_):
        self._compute_az_el = f_compute_az_el_

    def compute_az_el(self):
        """
        Refreshes the (az, el) values and returns them as an AzEl
        """
        return self._compute_az_el()


class OffsetPositionModel(PositionModel):
    def __init__(self, f_compute_az_el_, offset_):
        PositionModel.__init__(self, f_compute_az_el_)
        self._offset = offset_

    def compute_az_el(self):
        return PositionModel.compute_az_el(self) + self._offset


class AzimuthScaledOffsetPositionModel(PositionModel):
    def __init__(self, f_compute_az_el_, offset_):
        PositionModel.__init__(self, f_compute_az_el_)
        self._offset = offset_

    def compute_az_el(self):
        pos = PositionModel.compute_az_el(self)
        el_scale = cos(radians(pos.get_elevation() + self._offset.get_elevation()))
        if el_scale:
            # scaling with elevation only works for -180<=azimuth<=180
            # but AzEl uses 0<=azimuth<360
            az = self._offset.get_azimuth()
            if az > 180:
                az -= 360
            return AzEl(pos.get_azimuth() + az/el_scale,
                        pos.get_elevation() + self._offset.get_elevation())
        else:  # el_scale=0 so azimuth not important
            return AzEl(pos.get_azimuth(),
                        pos.get_elevation() + self._offset.get_elevation())
