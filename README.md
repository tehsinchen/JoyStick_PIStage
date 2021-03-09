# JoyStick_PIstage

In this work, the joystick made by tkinter controls the PI stage.
![image](https://github.com/tehsinchen/JoyStick_PIstage/blob/main/demo/JoyStick_PIStage.gif)

## Video description

In the beginning, a popup window asks for the serial numbers of PI stage. The program automatically detects the name of the stage and shows it on the title of the window, e.g., C-867 and E-518.
In order to make the operation on the joystick consistent with the live image from the camera, you can adjust:
```
self.x = self.stage.axes[1]
self.y = self.stage.axes[0]
```
for changing the axes controlled by joystick, and
```
if self.nb_axis == 3:
    time_unit = 10
    increment_x = -self.increment_x
    increment_y = self.increment_y
    unit = self.stage.qVEL(self.x)[self.x]
else:
    unit = 0.05
    time_unit = 500
    increment_x = self.increment_x
    increment_y = -self.increment_y
    self.stage.VEL(self.x, unit*abs(increment_x))
    self.stage.VEL(self.y, unit*abs(increment_y))
```  

to change the direction (self.increment) and steps (unit).

The z-axis of the stage can be controlled by the mousewheel, i.e., in the end of the video. As long as the mouse is inside the correct window, in this case E-518, and not on the dot, the mousewheel can adjust the height of the stage. 

The movement can be smoother by adjusting the velocity of stage, there will be no jittering if a good combination of unit and velocity is found.

