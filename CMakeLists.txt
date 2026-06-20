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
  "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp/pll.cpp")

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
  src/cpp/csr_graph.cpp
  src/cpp/scc.cpp
  src/cpp/levels.cpp
  src/cpp/minpost.cpp
  src/cpp/bfsdfs.cpp
  src/cpp/grail.cpp
  src/cpp/feline.cpp
  src/cpp/pll.cpp)
target_include_directories(cpp_tests PRIVATE
  src/cpp/include src/cpp/tests)
add_test(NAME cpp_tests COMMAND cpp_tests)
