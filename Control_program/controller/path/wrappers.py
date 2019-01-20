from controller.path.pathfinding import path_finder


class PFNode:
    def __init__(self, node_id, node_obj):
        self._id = node_id
        self._obj = node_obj

    def position(self):
        return self._obj.position()

    def azimuth(self):
        return self.position().get_azimuth()

    def elevation(self):
        return self.position().get_elevation()


class AbstractPathFinderWrapper:
    def __init__(self, nodes, start_node, f_node_dist, max_batch_size_):
        """
        min_el_sectors and max_batch_size are used to reduce number of nodes
        to solve for by solving the problem in smaller batches, which are
        joined to form a complete solution.
        """
        self._start_node = start_node
        self._f_node_dist = f_node_dist
        self._max_batch_size = max_batch_size_
        self.update_nodes(nodes)

    def section_find_path(self, path):
        raise NotImplementedError("Abstract Method")

    def path_length(self, path):
        raise NotImplementedError("Abstract Method")

    def distance(self, i, j):
        raise NotImplementedError("Abstract Method")

    def _all_nodes(self):
        nlist = [self._start_node]
        nlist.extend(self._nodes)
        return nlist

    def get_nodes(self):
        return self._nodes

    def update_nodes(self, nodes):
        self._nodes = nodes

    def find_optimal_path(self):
        """
        attempts to find an path where all nodes are visited while moving the
        shortest distance.
        This problem is NP-hard to solve and scales as O(n!).
        See https://en.wikipedia.org/wiki/Travelling_salesman_problem
        """
        start_path = sorted([PFNode(i, n) for i, n in enumerate(self.get_nodes())],
                            key=PFNode.azimuth)
        if not start_path:
            return list(), 0
        self._insert_start_node(PFNode(0, self._start_node), start_path)
        optim_path, oplen = self._find_optimal(start_path)

        # only remove start node if there are more nodes in the path
        # if the acutal path only has one node and it happens be the
        # same as the start node, they are considered to be the same
        # node.
        return [p-1 for p in optim_path], oplen

    def _find_closest(self, node, nodes, f_dist):
        """
        finds the node in nodes that is cloest to node according to f_dist
        """
        distances = [f_dist(node.position(), n.position()) for n in nodes]
        return nodes[distances.index(min(distances))]

    def _rotate_nodes(self, zeroth_node, nodes):
        """
        rotate nodes in-place untill zeroth_node is the 0th node in nodes
        """
        while nodes[0] is not zeroth_node:
            nodes.append(nodes.pop(0))

    def _insert_start_node(self, node, path):
        """
        rotate path such that the first element in path is the closest to node.
        Then insert node at the beginning of path.
        node ids are incremented to reflect the insertion.
        """
        self._rotate_nodes(self._find_closest(node, path, self._f_node_dist), path)
        for p in path:
            p._id += 1
        path.insert(0, node)

    def _find_optimal(self, path):
        """
        finds them shortest path for each path in paths and joins them.
        together into a single path.
        It is recommended that paths is sorted to provide a good initial
        guess.
        """
        if len(path) > self._max_batch_size:
            paths = self._split_to_batches(path, self._max_batch_size)
            sector_optimal_paths = list()
            for p, next_path in zip(paths[:-1], paths[1:]):
                sector_optimal_paths.append(self.section_find_path(p))
                next_path.insert(0, sector_optimal_paths[-1][-1])
            sector_optimal_paths.append(self.section_find_path(paths[-1]))
            optimal_path = [i for po in sector_optimal_paths for i in po[1:]]
        else:
            optimal_path = self.section_find_path([p._id for p in path])[1:]
        return optimal_path, self.path_length(optimal_path)

    def _split_to_batches(self, path, max_size):
        """
        splits path into batches until all batches are
        <max_size in size.
        """
        return [[e._id for e in p] for p in self._partition(path, max_size)]

    def _partition(self, l, max_size):
        """
        partitions l into equally sized partitions (where possible) until each
        partition has <max_size elements in it.
        """
        if len(l) > max_size:
            mid = int(len(l)/2)
            return self._partition(l[:mid], max_size) + self._partition(l[mid:], max_size)
        else:
            return [l]


class PathFinderWrapper(AbstractPathFinderWrapper):
    def section_find_path(self, path):
        pf_path = path_finder.pf_path_i()
        for p in path:
            pf_path.push_back(p)
        path_optim = path_finder.find_paths(self._m_dist_mat, pf_path)
        return [path_optim.get(i) for i in xrange(path_optim.size())]

    def path_length(self, path):
        pf_path = path_finder.pf_path_i()
        for p in path:
            pf_path.push_back(p)
        return path_finder.calc_path_length(self._m_dist_mat, pf_path)

    def distance(self, i, j):
        return self._m_dist_mat.get(i, j)

    def update_nodes(self, nodes):
        AbstractPathFinderWrapper.update_nodes(self, nodes)
        nl = self._all_nodes()
        self._m_dist_mat = path_finder.pf_matrix_d(len(nl))
        for i, ni in enumerate(nl):
            for j, nj in enumerate(nl):
                self._m_dist_mat.set(i, j, self._f_node_dist(ni.compute_az_el(),
                                                             nj.compute_az_el()))
