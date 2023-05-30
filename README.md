<p align="center"><img src="Resources/LOGO.png" width = "200" height = "200" alt="LOGO"/></p>

# <p align="center"><b>HAND WIGI</b></p>

<p align="center">A hand recognition&amp;interaction app based on mediapipe and OpenCV.</p>

## Get started

  Release提供的完整包含有运行库，点击HAND WIGI.exe即可启动。
  
  启动前务必确保文件夹路径不含有中文，不然可能无法访问到mediapipe的路径。
  
  尽量保证手掌平面与相机取相平面平行，环境光适宜，识别效果最佳。尤其是在鼠标控制功能下需要较高的识别精度来获得较好的效果。
  
## Manual

1. 手势识别部分以烂大街的向量方法为基础
- 通过手指关节点构建向量，设定角度阈值，以向量夹角大小与阈值判断手指是否弯曲，通过各个手指的弯曲状况判定手势。
- 增设了对于Thumb Up/Down的区别判断，其实就是判断拇指尖相对掌心位置即可。
- 增设了对于OK手势的辅助判断，因为OK手势食指和拇指尚未达到弯曲阈值
2. 
3. 
