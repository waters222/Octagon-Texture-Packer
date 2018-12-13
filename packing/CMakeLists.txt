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
        )


find_package(Threads REQUIRED)
find_package(OpenCL REQUIRED)

if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    add_definitions("-DWINDOWS")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    add_definitions("-DLINUX")
endif()

add_executable(Packing ${SOURCE_FILES})
target_link_libraries(Packing OpenCL::OpenCL ${CMAKE_THREAD_LIBS_INIT})