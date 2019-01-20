#include <vector>
#include <list>
#include <tuple>
#include <algorithm>

#include "path_finder.hpp"

using namespace std;

static constexpr double INFTY = 1e10;

using path_t = uint_fast8_t;

struct shortest {
  double l;
  vector<path_t> p;
};

struct candidate {
  double l;
  vector<path_t> &p;
  candidate operator+(double d) { return {l+d, p}; }
  candidate &operator+=(double d) { l += d; return *this; }
};

inline bool operator<(candidate const &lhs, shortest const &rhs) { return lhs.l < rhs.l; }
inline bool operator<(shortest const &lhs, candidate const &rhs) { return lhs.l < rhs.l; }

class path_finder {
public:
  path_finder(pf_matrix<double> const &node_dist) : _dist(node_dist) { }

  tuple<vector<path_t>, double>
  find_path(vector<path_t> const &path) {
    s = {INFTY, {}};
    vector<path_t> p{path};
    find_optimal_path({0.0, p}, p.size(), p.begin());
    return tuple<vector<path_t>, double>{s.p, s.l};
  }
  
private:
  pf_matrix<double> const _dist;
  shortest s;

  void
  find_optimal_path(candidate c,
		    size_t const size,
		    vector<path_t>::iterator const bgn)
  {
    if (s < c) {
      return;
    }
    if (size == 2) {
      c += _dist.at(*bgn, *next(bgn));
      if (c < s) {
	s = {c.l, c.p};
      }
    } else if (size > 2) {
      for (auto i{size}; --i; rotate(next(bgn), next(next(bgn)), c.p.end())) {
	find_optimal_path(c + _dist.at(*bgn, *next(bgn)), size-1, next(bgn));
      }
    }
  }
};

static vector<path_t>
pf_path_to_list(pf_path<int> const &in)
{
  vector<path_t> out;
  for (auto &i : in.stl()) { out.push_back(i); }
  return out;
}

static pf_path<int>
pf_path_from_list(vector<path_t> const &in)
{
  pf_path<int> out;
  for (auto &v : in) { out.push_back(v); }
  return out;
}

extern pf_path<int>
find_paths(pf_matrix<double> const &node_mat,
	   pf_path<int> const &path)
{
  auto optimal_path{path_finder(node_mat).find_path(pf_path_to_list(path))};
  return pf_path_from_list(get<0>(optimal_path));
}

extern double
calc_path_length(pf_matrix<double> const &node_mat,
		 pf_path<int> const &path)
{
  double plen = 0;
  for (size_t i = 0, j = 1; j < path.size(); ++i, ++j) {
    plen += node_mat.at(path.at(i), path.at(j));
  }
  return plen;
}
