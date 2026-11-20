cmake_minimum_required(VERSION 3.20)
project(window_bridge LANGUAGES C OBJC)

set(CMAKE_OBJC_STANDARD 11)
set(CMAKE_OBJC_STANDARD_REQUIRED ON)

find_library(COCOA_LIBRARY Cocoa REQUIRED)

add_library(window_bridge SHARED
        someui/crossplatform/window_loops/macos/window_bridge.m
)

target_compile_options(window_bridge PRIVATE
        -fobjc-arc
        -fvisibility=hidden
)

target_link_libraries(window_bridge PRIVATE
        ${COCOA_LIBRARY}
)

# На macOS для .dylib обычно удобнее без префикса lib (или оставь как есть, если ждёшь libwindow_bridge.dylib)
set_target_properties(window_bridge PROPERTIES
        PREFIX ""
        SUFFIX ".dylib"
)