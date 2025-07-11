cmake_minimum_required(VERSION 3.5)
project(drt_ur_gui)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(python_qt_binding REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(
  DIRECTORY ui launch resources
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
    scripts/run_gui.py
    scripts/run_mock_dbc.py
    DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})

ament_package()
