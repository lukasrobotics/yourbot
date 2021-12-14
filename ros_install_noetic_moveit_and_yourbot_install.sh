#!/bin/bash -eu
# The BSD License


name_ros_distro=noetic 
user_name=$(whoami)
echo "#######################################################################################################################"
echo ""
echo "ROS Noetic + Moveit + YourBot Installation, can take up to three or four hours"
version=`lsb_release -sc`
relesenum=`grep DISTRIB_DESCRIPTION /etc/*-release | awk -F 'Ubuntu ' '{print $2}' | awk -F ' LTS' '{print $1}'`
echo ">>> {Ubuntu version is: [Ubuntu $version $relesenum]}"
case $version in
  "focal" )
  ;;
  *)
    echo "ERROR:script will only work on Focal (20.04)"
    exit 0
esac
echo "#######################################################################################################################"
echo "1: Configure  Ubuntu "
echo ""
sudo add-apt-repository universe
sudo add-apt-repository restricted
sudo add-apt-repository multiverse
echo ""
echo "#######################################################################################################################"
echo " 2: Setup sources.list"
echo ""
sudo sh -c "echo \"deb http://packages.ros.org/ros/ubuntu ${version} main\" > /etc/apt/sources.list.d/ros-latest.list"
if [ ! -e /etc/apt/sources.list.d/ros-latest.list ]; then
  echo "Error: Unable to add sources.list"
  exit 0
fi
echo ""
echo "#######################################################################################################################"
echo " 3: Set up  keys"
sudo apt install curl
echo "#######################################################################################################################"
echo ""
ret=$(curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC1CF6E31E6BADE8868B172B4F42ED6FBAB17C654' | sudo apt-key add -)
case $ret in
  "OK" )
  ;;
  *)
    echo ">>> {ERROR: Unable to add ROS keys}"
    exit 0
echo ""
echo "#######################################################################################################################"
echo "4: Updating, this will take few minutes"
echo ""
sudo apt update
package_type="desktop-full"
echo "#######################################################################################################################"
echo ""
#echo "starting installation"
#echo ""
sudo apt-get install -y ros-${name_ros_distro}-${package_type} 
#echo ""
#echo ""
echo "#######################################################################################################################"
echo "6" 
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
echo "#######################################################################################################################"
echo "8: start ROS setup"
sudo apt-get update
echo "#######################################################################################################################"
echo "9"
sudo apt-get install -y python3-catkin-tools
echo "#######################################################################################################################"
echo "10"
#source /opt/ros/noetic/setup.bash
echo "#######################################################################################################################"
echo "11"
cd 
mkdir -p ~/catkin_ws/src 
echo "#######################################################################################################################"
echo "12"
cd ~/catkin_ws/
echo "#######################################################################################################################"
echo "13: run catkin_make"
catkin_make
echo "#######################################################################################################################"
echo "14"
source devel/setup.bash
echo "#######################################################################################################################"
echo "15:"
echo "start install moveit"
sudo apt install -y ros-noetic-moveit
echo "#######################################################################################################################"
echo "16"
sudo apt install -y python3-rosdep2
echo "#######################################################################################################################"
echo "17"
rosdep update
echo "#######################################################################################################################"
echo "18"
sudo apt update
echo "#######################################################################################################################"
echo "19"
sudo apt -y dist-upgrade
echo "#######################################################################################################################"
echo "20"
sudo apt install ros-noetic-catkin python3-catkin-tools python3-osrf-pycommon
echo "#######################################################################################################################"
echo "21"
sudo apt install -y python3-wstool
echo "#######################################################################################################################"
echo "22"
mkdir -p ~/ws_moveit/src
echo "#######################################################################################################################"
echo "23"
cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "24"
wstool init . || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "25"
wstool merge -t . https://raw.githubusercontent.com/ros-planning/moveit/master/moveit.rosinstall || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "26"
wstool remove  moveit_tutorials || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "27" 
wstool update -t . || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "28"
cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "29"
git clone https://github.com/ros-planning/moveit_tutorials.git -b master || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "30"
git clone https://github.com/ros-planning/panda_moveit_config.git -b melodic-devel || cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "31"
cd ~/ws_moveit/src
echo "#######################################################################################################################"
echo "32"
rosdep install -y --from-paths . --ignore-src --rosdistro noetic
echo "#######################################################################################################################"
echo "33"
sudo sh -c 'echo "deb http://packages.ros.org/ros-testing/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
echo "#######################################################################################################################"
echo "34"
sudo apt update
echo "#######################################################################################################################"
echo "35"
echo "start building"
echo "#######################################################################################################################"
echo "36"
cd ~/ws_moveit
echo "#######################################################################################################################"
echo "37"
catkin config --extend /opt/ros/${ROS_DISTRO} --cmake-args -DCMAKE_BUILD_TYPE=Release
echo "#######################################################################################################################"
echo ">>>38: build moveit packages, this can take up too three hours. so go do something else"
catkin build --jobs 2
echo "#######################################################################################################################"
echo "39 install lib"
sudo apt-get install -y python3-pip
echo "#######################################################################################################################"
echo "40 install lib"
sudo pip install pyinstaller
echo "#######################################################################################################################"
echo "41: remove old demo.launch"
cd ~/ws_moveit/src/panda_moveit_config/launch # directory of panda_config files
rm demo.launch || cd ~/ws_moveit/src/panda_moveit_config/launch
echo "#######################################################################################################################"
echo "42: clone github repository"
cd ~/ws_moveit
git clone https://github.com/lukasrobotics/yourbot || cd ~/ws_moveit
echo "#######################################################################################################################"
echo "43: create custome demo.launch file"
cd ~/ws_moveit/yourbot # directory of changed demo.launch file
mv demo.launch ~/ws_moveit/src/panda_moveit_config/launch || cd ~/ws_moveit/yourbot
echo "#######################################################################################################################"
echo "44: creating programm links"
cd ~/ws_moveit/yourbot/yourbot_build
chmod u+x yourbot_build
ln -s ~/ws_moveit/yourbot/yourbot_build/yourbot_build ~/ws_moveit || cd ~/ws_moveit/yourbot/yourbot_build
cd ~/ws_moveit
chmod u+x yourbot_build

sudo reboot




