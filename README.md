Wallpaper-Splitter
==================

Wallpaper-splitter is an application for splitting large images up into smaller images to be used for desktop backgrounds.

The Itch?
-------
Every program is created to scrach an itch.   In my this case, I was getting
really tired of using GIMP to break large wallpapers apart.  My monitor configuration
is non-standard and my monitors are not all the same size.  I wrote wallpaper-splitter
to easily break my wallpapers apart so I can apply them on individual monitors to form
a unified image.  Hopefully it can help you do the same.

Monitor Definition Files
---------
First you need to make a monitor definition JSON file.  An example is shown here:
```
{
   "comment": "Inverted T composed of 4 1920x1200 monitors",

   "monitors":
   [
      {"name": "Top",
       "resolution": [1920, 1200],
       "upper_left": [1920, 0],
       "suffix": "_1"
      },
      {"name": "Left",
       "resolution": [1920, 1200],
       "upper_left": [0, 1200],
       "suffix": "_2"
      },
      {"name": "Middle",
       "resolution": [1920, 1200],
       "upper_left": [1920, 1200],
       "suffix": "_3"
      },
      {"name": "Right",
       "resolution": [1920, 1200],
       "upper_left": [3840, 1200],
       "suffix": "_4"
      }
   ]
}

```
The resolution of each monitor should be given in pixels along with the coordinate of the upper left
pixel.  The coordinate system has (0,0) in the upper left in the form of (x,y).  y grows positive as it grows
down.

If this seems a little hard to visualize simply convert an image with wallpaper-splitter and it will print
out a representation of the given monitor configuration.  For example, lets use this example monitor definition file
to split an image:
```
> python3 src/wallpaper-splitter.py -m \
> resources/monitor_defs/inverted_T_1920x1200.json image.jpg
Monitor Layout read from definition file:
                          +-------------------------+                          +
                          |Top                      |                          ^
                          |1920x1200                |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          2
                          |                         |                          4
+-------------------------+-------------------------+-------------------------+0
|Left                     |Middle                   |Right                    |0
|1920x1200                |1920x1200                |1920x1200                ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
+-------------------------+-------------------------+-------------------------+V
+<-----------------------------------5760------------------------------------->+
Processing:  image.jpg

Projection of monitor definition file onto image.jpg:
                                                                               +
                                                                               ^
                                                                               |
                                                                               |
                          +-------------------------+                          |
                          |Top                      |                          |
                          |1920x1200                |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          2
                          |                         |                          5
+-------------------------+-------------------------+-------------------------+6
|Left                     |Middle                   |Right                    |0
|1920x1200                |1920x1200                |1920x1200                ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
+-------------------------+-------------------------+-------------------------+|
                                                                               |
                                                                               |
                                                                               V
+<-----------------------------------4096------------------------------------->+
>
```

Dependencies
------
Wall-paper splitter has the following dependencies:
   - Python3
   - Pillow (https://pillow.readthedocs.org/)

Algorithm
------
Wallpaper-splitter tries its best to overlay the monitor configuration onto the
source image(s) provided.  It tries to stretch the monitors as large as possible
onto the image(s).  It will either bump up against the left/right or the top/bottom
of the image first.  As soon as that happens, it figures out how many pixels on the
image correspond to pixels on the monitor and then crops the image for each monitor.
After that, it scales the images to match the output for each monitor wallpaper
desired (unless told not to).

Controlling the Output
-------
You have some control over how wallpaper-splitter decides where to chop the image
apart.  Imagine if you are trying to overlay a 2 monitor high monitor definition
onto a very wide image.  Wallpaper-splitter would be limited very quickly by
the height of the image but would have a lot of freedom to choose from for
the location horizontally to overlay.  You can use the positional arguments to affect
where wallpaper-splitter places the overlay before cropping.

Looking at the help:
```
usage: wallpaper-splitter.py [-h] --monitor <monitor_def_file.json> [--quiet]
                             [--verbose]
                             [--left | --right | --left-padding LEFT_PADDING | --right-padding RIGHT_PADDING]
                             [--top | --bottom | --top-padding TOP_PADDING | --bottom-padding BOTTOM_PADDING]
                             [--crop_only]
                             img_file [img_file ...]

Wallpaper-Splitter

positional arguments:
  img_file              Image files to convert

optional arguments:
  -h, --help            show this help message and exit
  --monitor <monitor_def_file.json>, -m <monitor_def_file.json>
                        Monitor Layout Definition JSON File
  --quiet, -q           Quiet Output
  --verbose, -v         Verbose Output

Crop Padding:
  --left                Left justify the cropped images
  --right               Right justify the cropped images
  --left-padding LEFT_PADDING
                        Left Padding value
  --right-padding RIGHT_PADDING
                        Right Padding value
  --top                 Top justify the cropped images
  --bottom              Bottom justify the cropped images
  --top-padding TOP_PADDING
                        Top Padding value
  --bottom-padding BOTTOM_PADDING
                        Bottom Padding value

Step Selection:
  --crop_only           Do not resize the output images. Crop only

```

--left, --right, --left-padding, --right-padding, --top, --bottom, --top-padding, and --bottom-padding can
be used to slide the layout window.

Putting it All Together
--------
After you have created a monitor definition file, simply tell wallpaper-splitter to split your images for you:
```
> python3 src/wallpaper-splitter.py -m resources/monitor_defs/6_monitors.json \
> image.jpg --left-padding 3800
Monitor Layout read from definition file:
                          +-------------------------+                          +
                          |Top                      |                          ^
                          |1920x1200                |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          2
                          |                         |                          4
+-------------------------+-------------------------+-------------------------+0
|Left                     |Middle                   |Right                    |0
|1920x1200                |1920x1200                |1920x1200                ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
+-------------------------+-------------------------+-------------------------+V
+<-----------------------------------5760------------------------------------->+
Processing:  image.jpg

Projection of monitor definition file onto image.jpg:
                                                                               +
                                                                               ^
                                                                               |
                                                                               |
                          +-------------------------+                          |
                          |Top                      |                          |
                          |1920x1200                |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          |
                          |                         |                          2
                          |                         |                          5
+-------------------------+-------------------------+-------------------------+6
|Left                     |Middle                   |Right                    |0
|1920x1200                |1920x1200                |1920x1200                ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
|                         |                         |                         ||
+-------------------------+-------------------------+-------------------------+|
                                                                               |
                                                                               |
                                                                               V
+<-----------------------------------4096------------------------------------->+
>
```

TODO
----
 - GUI?
 - ~~Show layout overlay on image?~~
 - Re-implement as a Gimp Plugin?
 - Start a collection of Monitor Definition Files?

Notes:
-----
There is nothing about wallpaper-splitter that makes it specific to wallpapers.
It could be used to split feeds from a webcam, etc.

Patches are welcome.

Thanks,

Barry

