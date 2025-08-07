# `drt_ur_gui`
`drt_ur_gui` is a ROS 2 based user interface written in python that enables remote operation of Universal Robotics collaborative robotic arms. 
- Intended to be used with UR Arms configured for Remote Control
- Enables command of UR Arms with out Polyscope touchscreen pendant interaction
- Useful in operations where Polyscope interaction is difficult or unsafe



## Installation
Installation of `drt_ur_gui` is similar to most ROS 2 packages.
1) Clone `drt_ur_gui` into your workspace `src/` directory
2) Use rosdep install `drt_ur_gui`'s dependencies
3) Build your workspace
```bash
cd src/
git clone git@js-er-code.jsc.nasa.gov:imetro/drt_ur_gui.git
rosdep install -iy --from-paths . --rosdistro=humble
cd ..
colcon build
```

## Use
On it's own `drt_ur_gui` is configured to command up to two URs at once using launch files (though it can be used to command more)
#### One arm use
- `one_arm.launch.py` is used to run a singular UR arm
    - `ros2 launch drt_ur_gui one_arm.launch.py`
    - Configured by `config/one_arm.yaml`
        - YAML Configured Parameters:
            - `dashboard_client_name`: name of the UR `dashboard_client` node, must match or UR communication will fail
            - `program`: sets the default program to be loaded to the UR when `/dashboard_client/load_program` is selected
            - `window.name`: sets the name that appears in the bar at the top of the UI window
            - `window.stylesheet`: Qt format stylesheet, enables users to customize the look and feel of the UI
            - `logo_file_name`: the filepath to the logo to be displayed in the UI window
#### Two arm use
- `two_arm.launch.py` is used to run two URs at once, typically in a "humanoid" left-right configuration
    - `ros2 launch drt_ur_gui two_arm.launch.py`
    - Configured by `config/two_arm_left.yaml` and `config/two_arm_right.yaml`
        - Parameters exposed in the two arm configuration files are the same as the one arm configuration parameters explained above
#### *N* arm use and use with other robots
- `drt_ur_gui` can command any number of UR arms in (probably) any robot setup
    - Every `drt_ur_gui` backend node communicates with an arm's respective `dashboard_client` node
    - The UI can be run from the command line without configuration files as long as the correct `dashboard_client` node name is provided as a parameter
        - `ros2 run drt_ur_gui run_gui.py --ros-args -p dashboard_client_name:=<your_dashboard_client_name>`
    - Alternatively, and similar to the launch files, a full configuration/parameters file can be used if you provide the path
        - `ros2 run drt_ur_gui run_gui.py --ros-args --params-file <path_to_your_params_file>`
    - `drt_ur_gui` can also be integrated into your robot's existing launch files
        - Use the provided launch files as and example


## Notes
- UR pendantless operations:
    - has a procedure that does all the service calls (this is the real concept of the backend). Needs to stress test it and want folks to use the procedure when running CLR and phoebe. 
- QT vs tkinter - what do we do? 
    - emma leans towards pyqt and ros_qt_bindings
    - appearance does matter because this is a need in the community
- Remapping and renaming
    - Nodes can be renamed from the command line using ros-args (assuming you passed them in your script)
    - `ros2 run drt_ur_gui run_mock_dbc.py --ros-args -r __node:=right_dashboard_client`
        - Runs the mock dashboard client node but with the name `right_dashboard_client`
        - Everything (services and stuff) get renamed too