cmake_minimum_required(VERSION 3.20)
project(crud_task)

set(CMAKE_CXX_STANDARD 26)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z execstack -no-pie")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} \
    -O0 \
    -fno-stack-protector \
    -D_FORTIFY_SOURCE=0 \
    -fno-pie \
    -no-pie \
    -z execstack \
    -fno-asynchronous-unwind-tables \
    -fcf-protection=none \
    -mno-sse \
    -fno-stack-clash-protection \
    -fno-sanitize=all \
    -fno-omit-frame-pointer \
    -fno-strict-aliasing \
    -fno-strict-overflow \
    -fno-delete-null-pointer-checks \
    -fno-isolate-erroneous-paths-dereference")

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z execstack -no-pie -z norelro -z lazy")


find_path(ASIO_INCLUDE_DIR asio.hpp REQUIRED)
include_directories (SYSTEM "${ASIO_INCLUDE_DIR}")
add_executable(crud_task main.cpp)
