from copy import copy
from time import time

from numpy import arange

from controller.util import AzEl
from controller.satellites.posmodel import AzimuthScaledOffsetPositionModel


class EmptyPath(RuntimeError):
    pass


class PathStrategy:
    def find_optimal_path(self, refresh=True):
        raise NotImplementedError("Abstract Method")


class CelestialObjectMapping(PathStrategy):
    """

    use satellites.CelestialObject. creates path that is
    a grid around a celestial object (e.g. the sun).
    """
    def __init__(self, logger_, rows_=9, cols_=9, rstep_=1.5, cstep_=1.5):
        self._logger = logger_
        self._rows = rows_
        self._cols = cols_
        self._rstep = rstep_
        self._cstep = cstep_
        self._ref_obj = None
        self._grid_path = list()
        self._sat_path = list()
        self._begin = 0
        self._end = 0
        self._itr = self._end

    def set_target(self, target_):
        self._ref_obj = target_

    def set_rows(self, rows_):
        self._rows = rows_

    def set_cols(self, cols_):
        self._cols = cols_

    def set_row_step(self, rstep_):
        self._rstep = rstep_

    def set_col_step(self, cstep_):
        self._cstep = cstep_

    def _compute_path(self):
        grid_path = list()
        path = list()
        do_reverse = False
        for i, r in enumerate((arange(self._rows) - (self._rows-1)/2.0)*self._rstep):
            gp = list()
            p = list()
            for j, c in enumerate((arange(self._cols) - (self._cols-1)/2.0)*self._cstep):
                gp.append((i, j))
                p.append(self._ref_obj.copy(
                    self._ref_obj.name() + "_%.3f_%.3f" % (r, c),
                    AzimuthScaledOffsetPositionModel(self._ref_obj.compute_az_el,
                                                     AzEl(c, r))
                ))
            if do_reverse:
                p.reverse()
                gp.reverse()
            path.append(p)
            grid_path.append(gp)
            do_reverse = not do_reverse

        self._grid_path = list()
        self._sat_path = list()
        for p, gp in zip(path, grid_path):
            self._sat_path.extend(p)
            self._grid_path.extend(gp)
        l_path_ = (self._cols-1)*self._rows*self._cstep + (self._rows-1)*self._rstep
        return self._sat_path, l_path_

    def find_optimal_path(self, refresh=True):
        return self._compute_path()

    def __iter__(self):
        self._begin = 0
        self._end = len(self._sat_path)
        self._itr = self._begin
        return self

    def next(self):
        if self._itr == self._end:
            raise StopIteration
        out = self._sat_path[self._itr]
        self._itr += 1
        return out

    def get_current_grid_point(self):
        return self._grid_path[self._itr-1]


class PathFindingManager:
    def __init__(self, logger_, sat_pos_comp_, pf_wrapper_,
                 satellites_, constellations_, el_cutoff_angle_):
        self._logger = logger_
        self._sat_pos_comp = sat_pos_comp_
        self._satellites = dict()

        self._target_satellites = satellites_
        self._target_constellations = constellations_
        self._el_cutoff_angle = el_cutoff_angle_
        self._pf = pf_wrapper_

        self._current_iter = None

    def sat_in_path(self):
        self._refresh_satellites()
        return len(self._satellites)

    def _filter_el(self, s):
        return [n for n in s if n.position().get_elevation() >= self._el_cutoff_angle]

    def __iter__(self):
        self._refresh_satellites()
        self._current_iter = copy(self._satellites.values())
        if not self._filter_el(self._current_iter):
            raise EmptyPath("No satellites in path")
        return self

    def next(self):
        if not self._current_iter:
            raise StopIteration
        self._pf.update_nodes(self._filter_el(self._current_iter))

        t0 = time()
        path, plen = self._pf.find_optimal_path()
        t1 = time()
        if not path:
            self._current_iter = list()
            raise StopIteration
        self._logger.info("PathFinding took %.3f ms" % (1e3*(t1-t0)))
        self._logger.debug("Path: " + str([self._pf.get_nodes()[i].name() for i in path]))
        sat = self._get_satellites_from_path(path)[0]
        self._current_iter.remove(sat)
        return sat

    def find_optimal_path(self, refresh=True):
        """
        (re)loads the satellites if necessary/requested and computes
        the optimal path to take so that all satellites are visited
        while moving as little as necessary.
        """
        if refresh or len(self._satellites) == 0:
            self._refresh_satellites()

        t0 = time()
        path, plen = self._pf.find_optimal_path()
        t1 = time()

        sat = self._pf.get_nodes()
        self._logger.info("PathFinding took %.3f ms" % (1e3*(t1-t0)))
        """
        self._logger.debug("Path: " + str([sat[i].name() for i in path]))
        self._logger.debug("Path length: %.3f radians (%.1f degrees, %.2f rotations)"
                           % (plen, degrees(plen), plen/(2*pi)))
        """
        return self._get_satellites_from_path(path), plen

    def _refresh_satellites(self):
        """
        reloads the satellites position and their visibility.
        """
        self._satellites.clear()

        for sys_name in self._target_constellations:
            if sys_name:
                self._satellites.update(self._sat_pos_comp.load_satellites(
                    sys_name, self._el_cutoff_angle))

        for sat_name in self._target_satellites:
            if sat_name:
                self._satellites.update({sat_name: self._sat_pos_comp.load_satellite(sat_name)})

        self._pf.update_nodes(self._filter_el(self._satellites.values()))

    def _get_satellites_from_path(self, path):
        """
        translates satellite node id into the corresponding satellite objects.
        """
        sat = self._pf.get_nodes()
        return [sat[i] for i in path]
