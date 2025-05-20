# DRT UR GUI
The DRT UR GUI is a ROS2 based user interface that enables remote Universal Robotics arm operations.

## Installation
Just clone it in to your workspace and build. If you have trouble try rosdepping.
```bash
rosdep update
rosdep check -i --from-paths <your workspace source dir> --rosdistro=humble
rosdep install -iy --from-paths <your workspace source dir> --rosdistro=humble
```

## Use
Currently all you can do in the GUI is make a selection of service calls.
- brake release
    - Calls `/dashboard_client/brake_release`
    - Brings the UR to RUNNING (green circle) mode
- 


## Notes
- UR pendantless operations:
    - has a procedure that does all the service calls (this is the real concept of the backend). Needs to stress test it and want folks to use the procedure when running CLR and phoebe. 
- QT vs tkinter - what do we do? 
    - emma leans towards pyqt and ros_qt_bindings
    - appearance does matter because this is a need in the community
 
 