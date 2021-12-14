# yourbot
code library for robotics and AI.

By using this platform/programm you agree to our terms of condition.

Requirements:
RaspberryPi4 with minimum 4GB RAM
Ubuntu 20.04 64-Bit(important) with xubuntu-desktop version


 ROS + Moveit + YourBot Installation
 get the 'install_ros_moveit_yourbot.sh' file on your RaspberryPi4 


```
chmod +x install_ros_moveit_yourbot.sh
```

then for installation:
```
./install_ros_moveit_yourbot.sh
```

Installation problems:
- screen frezze can occour
- can fail from itself

Solution: Just restart the RaspberryPi and run it again. Till its completly finished

Programing:

node python file header:
#build data-start_
#enter the package name here: example_node
#enter all the dependencies here: rospy 
#enter if its a node or a launch file: py
#enter your config folder and file: panda_moveit_config demo.launch
#build data-end:

launch file header:
<!--
#enter the package name here: example_launch
#enter all the dependencies here: rospy 
#enter if its a node or a launch file: launch
#enter your config folder and file: panda_moveit_config demo.launch
-->
