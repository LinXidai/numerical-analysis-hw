cmake_minimum_required(VERSION 3.16)

project(VaseReconstruction LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (MSVC)
    add_compile_options(/W4 /utf-8)
endif()

set(LOCAL_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
set(LOCAL_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/lib")
set(GLUT_LIBRARY "${LOCAL_LIB_DIR}/glut32.lib")
set(GLUT_DLL "${LOCAL_LIB_DIR}/glut32.dll")

if (NOT EXISTS "${GLUT_LIBRARY}")
    set(GLUT_LIBRARY "${LOCAL_LIB_DIR}/glut.lib")
    set(GLUT_DLL "${LOCAL_LIB_DIR}/glut.dll")
endif()

if (NOT EXISTS "${GLUT_LIBRARY}")
    message(FATAL_ERROR "No glut32.lib or glut.lib found in ${LOCAL_LIB_DIR}")
endif()

add_executable(VaseReconstruction src/main.cpp)
target_include_directories(VaseReconstruction PRIVATE "${LOCAL_INCLUDE_DIR}")
target_link_libraries(VaseReconstruction PRIVATE
    opengl32
    glu32
    winmm
    "${GLUT_LIBRARY}"
)

add_custom_command(
    TARGET VaseReconstruction POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${GLUT_DLL}"
            "$<TARGET_FILE_DIR:VaseReconstruction>"
    COMMENT "Copying GLUT runtime DLL"
)
