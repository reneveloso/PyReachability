cmake_minimum_required(VERSION 3.15)
project(pyreachability LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

execute_process(
  COMMAND "${Python_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NUMPY_INCLUDE OUTPUT_STRIP_TRAILING_WHITESPACE)

# Locate Cython and transpile _core.pyx -> _core.cpp
set(PYX "${CMAKE_CURRENT_SOURCE_DIR}/src/pyreachability/_core.pyx")
set(CPP_OUT "${CMAKE_CURRENT_BINARY_DIR}/_core.cpp")

add_custom_command(
  OUTPUT "${CPP_OUT}"
  COMMAND "${Python_EXECUTABLE}" -m cython --cplus -3 "${PYX}" -o "${CPP_OUT}"
  DEPENDS "${PYX}"
  VERBATIM)

set(CORE_SOURCES
  "${CPP_OUT}"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/csr_graph.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/scc.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/levels.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/minpost.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/bfsdfs.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/grail.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/feline.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/pll.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/tc.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/treecover.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/bfl.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/chaincover.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/preach.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/twohop.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/tflabel.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/two_hop.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/tol.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/hl.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/oreach.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/threehop.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/pathhop.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/ferrari.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/dual.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/treesspi.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/gripp.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/pathtree.cpp")

python_add_library(_core MODULE ${CORE_SOURCES} WITH_SOABI)
target_include_directories(_core PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/include"
  "${NUMPY_INCLUDE}")

install(TARGETS _core DESTINATION pyreachability)

# ---- C++ unit tests ----
enable_testing()
add_executable(cpp_tests
  src/cpp/tests/test_csr_graph.cpp
  src/cpp/tests/test_scc.cpp
  src/cpp/tests/test_bfsdfs.cpp
  src/cpp/tests/test_grail.cpp
  src/cpp/tests/test_feline.cpp
  src/cpp/tests/test_pll.cpp
  src/cpp/tests/test_tc.cpp
  src/cpp/tests/test_treecover.cpp
  src/cpp/tests/test_bfl.cpp
  src/cpp/tests/test_chaincover.cpp
  src/cpp/tests/test_preach.cpp
  src/cpp/tests/test_twohop.cpp
  src/cpp/tests/test_tflabel.cpp
  src/cpp/tests/test_tol.cpp
  src/cpp/tests/test_hl.cpp
  src/cpp/tests/test_oreach.cpp
  src/cpp/tests/test_threehop.cpp
  src/cpp/tests/test_pathhop.cpp
  src/cpp/tests/test_ferrari.cpp
  src/cpp/tests/test_dual.cpp
  src/cpp/tests/test_treesspi.cpp
  src/cpp/tests/test_gripp.cpp
  src/cpp/tests/test_pathtree.cpp
  src/cpp/csr_graph.cpp
  src/cpp/scc.cpp
  src/cpp/levels.cpp
  src/cpp/minpost.cpp
  src/cpp/bfsdfs.cpp
  src/cpp/grail.cpp
  src/cpp/feline.cpp
  src/cpp/pll.cpp
  src/cpp/tc.cpp
  src/cpp/treecover.cpp
  src/cpp/bfl.cpp
  src/cpp/chaincover.cpp
  src/cpp/preach.cpp
  src/cpp/twohop.cpp
  src/cpp/tflabel.cpp
  src/cpp/two_hop.cpp
  src/cpp/tol.cpp
  src/cpp/hl.cpp
  src/cpp/oreach.cpp
  src/cpp/threehop.cpp
  src/cpp/pathhop.cpp
  src/cpp/ferrari.cpp
  src/cpp/dual.cpp
  src/cpp/treesspi.cpp
  src/cpp/gripp.cpp
  src/cpp/pathtree.cpp)
target_include_directories(cpp_tests PRIVATE
  src/cpp/include src/cpp/tests)
add_test(NAME cpp_tests COMMAND cpp_tests)
