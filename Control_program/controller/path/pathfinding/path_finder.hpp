#ifndef PATH_FINDER_HPP_INCLUDED
#define PATH_FINDER_HPP_INCLUDED

#include <vector>
#include <cstdlib>

template<typename T>
class pf_path
{
public:
  pf_path(size_t size=0) : _path(size) { }
  
  T get(size_t i) const { return _path.at(i); }
  T wget(int i) const { return _path.at(wrap(i)); }
  void set(size_t i, T v) { _path.at(i) = v; }
  void wset(int i, T v) { _path.at(wrap(i)) = v; }
  void push_back(T v) { _path.push_back(v); }
  
  size_t size() const { return _path.size(); }
  
  T &at(size_t i) { return _path[i]; }
  T const &at(size_t i) const { return _path[i]; }

  std::vector<T> const &stl() const { return _path; }
private:
  std::vector<T> _path;
  inline size_t wrap(int i) const { return (i + size()) % size(); }
};

template<typename T>
class pf_matrix {
public:
  pf_matrix(size_t size)
    : _mat_size_bits(get_best_mat_size_bits(size)),
      _mat_size(1 << _mat_size_bits),
      _mat(_mat_size*_mat_size),
      _size(size) {
    
  }

  size_t size() const { return _size; }
  T get(size_t i, size_t j) const { return _mat.at(index(i, j)); }
  void set(size_t i, size_t j, T v) { _mat.at(index(i, j)) = v; }
  T &at(size_t i, size_t j) { return _mat.at(index(i, j)); }
  T const &at(size_t i, size_t j) const { return _mat.at(index(i, j)); }

private:
  size_t const _mat_size_bits;
  size_t const _mat_size;
  std::vector<T> _mat;
  size_t const _size;

  static constexpr size_t get_best_mat_size_bits(size_t size) {
    size_t best_fit_bits = 0;
    while (size_t(1 << best_fit_bits) < size) {
      ++best_fit_bits;
    }
    return best_fit_bits;
  }

  size_t index(size_t i, size_t j) const { return (i << _mat_size_bits | j); }
};


extern pf_path<int>
find_paths(pf_matrix<double> const &node_mat,
	   pf_path<int> const &path);
extern double
calc_path_length(pf_matrix<double> const &node_mat,
		 pf_path<int> const &path);

#endif //PATH_FINDER_HPP_INCLUDED
