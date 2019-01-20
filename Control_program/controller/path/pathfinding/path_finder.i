%module path_finder
%{
#include "path_finder.hpp"
%}
%include "path_finder.hpp"
%template(pf_matrix_d) pf_matrix<double>;
%template(pf_path_i) pf_path<int>;
