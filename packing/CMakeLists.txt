cmake_minimum_required(VERSION 2.8.4)
project(Packing)

if (CMAKE_BUILD_TYPE STREQUAL Debug)
    add_definitions(-DDEBUG)
endif ()
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -Wall")


set(SRCROOT ${CMAKE_SOURCE_DIR})
file( GLOB SOURCE_FILES
        ${SRCROOT}/src/argvparser.cpp
        ${SRCROOT}/src/BrutalPacking.cpp
        ${SRCROOT}/Packing.cpp
        ${SRCROOT}/stdafx.cpp
        )

if(WINDOWS)
    add_definitions("-DWINDOWS")
elseif(LINUX)
    add_definitions("-DLINUX")
    include_directories("/usr/local/include")
    include_directories("/opt/local/include")
    LINK_DIRECTORIES("/usr/local/lib")
    LINK_DIRECTORIES("/opt/local/lib")
    LINK_DIRECTORIES("/usr/local/cuda-9.2/lib64/")
endif()


add_executable(Packing ${SOURCE_FILES})
target_link_libraries(Packing OpenCL pthread)