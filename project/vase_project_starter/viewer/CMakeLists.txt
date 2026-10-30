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

# The bundled GLUT libraries are 32-bit (x86); refuse to configure for x64,
# otherwise linking fails with LNK2019/LNK4272. Configure with: cmake -B build -A Win32
if (CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR
        "The bundled GLUT libraries in ${LOCAL_LIB_DIR} are 32-bit (x86), "
        "but this build is configured for 64-bit. "
        "Re-configure with: cmake -B build -A Win32")
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
