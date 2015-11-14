#!/usr/bin/env python
###############################################################################
# Copyright (C) 2014 - Barry Grussling
# Targetting Python3
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
#
###############################################################################
import argparse
import json
import os
import os.path
import sys

try:
   from PIL import Image
except:
   sys.exit("Please install Pillow (https://pillow.readthedocs.org/)")

Msg_level = 0
MONITOR_SCALE = 2 # 8x16 for a ``normal'' cursor so use a vertical scale factor
                  # of 2.  Only applies to Y coordinates.

def log_debug(*args, **kwds):
   """Log a debug message to the screen."""
   # In the future we can use Msg_level to support multiple -v, or whatever
   if Msg_level >= 7:
      print(*args, **kwds)

def parse_cmdline():
   """Do command line parsing stuff"""
   parser = argparse.ArgumentParser(description = 'Wallpaper-Splitter')

   # Base arguments
   parser.add_argument('--monitor', '-m', required=True,
                       metavar='<monitor_def_file.json>',
                       help="Monitor Layout Definition JSON File")
   parser.add_argument('--quiet', '-q', action='store_true',
                       help="Quiet Output")
   parser.add_argument("img_file", nargs='+',
                       help='Image files to convert')
   parser.add_argument("--verbose", '-v', action='store_true',
                       help='Verbose Output')

   # Crop group
   pos = parser.add_argument_group('Crop Padding')
   leftright = pos.add_mutually_exclusive_group()
   leftright.add_argument("--left", help="Left justify the cropped images",
                          action='store_true')
   leftright.add_argument("--right", help="Right justify the cropped images",
                          action='store_true')
   leftright.add_argument("--left-padding", help="Left Padding value",
                          type=int, action='store')
   leftright.add_argument("--right-padding", help="Right Padding value",
                          type=int, action='store')

   # Position mutually exclusive stuff
   topbot = pos.add_mutually_exclusive_group()
   topbot.add_argument("--top", help="Top justify the cropped images",
                       action='store_true')
   topbot.add_argument("--bottom", help="Bottom justify the cropped images",
                        action='store_true')
   topbot.add_argument("--top-padding", help="Top Padding value",
                       type=int, action='store')
   topbot.add_argument("--bottom-padding", help="Bottom Padding value",
                       type=int, action='store')

   # Stuff I don't know where to put
   steps = parser.add_argument_group('Step Selection')
   steps.add_argument("--crop_only",
                      help="Do not resize the output images.  Crop only",
                      action='store_true')

   # Now parse them dudes
   args = parser.parse_args()

   if args.verbose:
      global Msg_level
      Msg_level = 7

   log_debug(args)
   return args

def parse_monitor(monitor_file):
   """Make certain the monitors file looks good and return the monitor
      section of it."""
   # Handle them ~'s
   real_file = os.path.expanduser(monitor_file)
   if not os.path.isfile(real_file):
      sys.exit("Unable to find " + monitor_file)

   j = []
   with open(real_file, 'r') as f:
      j = json.load(f)

   if "monitors" not in j:
      sys.exit("Your JSON file appears to be not-well-formatted.")
   return j['monitors']

def get_terminal_width():
   """Return the width of the terminal.  80 if things go south."""
   columns = 80
   try:
      _, columns = os.popen('stty size', 'r').read().split()
   except:
      pass
   return int(columns)

def find_monitor_extremes(monitors):
   """Return the max width and max height of the monitors.

      We have to base this on both the position and the resolution
      and return the absolute extremes those give us."""

   max_width = 0
   max_height = 0
   assert len(monitors) > 0
   for monitor in monitors:
      right_edge = monitor["upper_left"][0] + monitor["resolution"][0]
      if right_edge > max_width:
         log_debug("Monitor", monitor["name"], "gives new max right edge",
                   right_edge)
         max_width = right_edge
      top_edge = monitor["upper_left"][1] + monitor["resolution"][1]
      if top_edge > max_height:
         log_debug("Monitor", monitor["name"], "gives new max height",
                   top_edge)
         max_height = top_edge
   log_debug("Monitor maximums:", [max_width, max_height])
   return max_width, max_height


def calculate_scale(monitors, output_width=None, output_height=None):
   """Calculate the Desired Monitor Layout.  output_width or output_height
      could be limiting factor."""

   # The basic idea here is to look at our monitors, find out how many
   # pixels there are in the X and the Y direction, and then figure out
   # which one will "bump" up against the output_* variables first.
   # After we figure that out, we can calculate the scale factor and the
   # "other" output_*.

   # We have to bump into SOMETHING first.
   assert output_width is not None or output_height is not None

   # We are either WIDTH or HEIGHT limited
   limiting_factor = None
   output_ratio = None

   # Find the extremes and the monitor ratio
   monitor_width, monitor_height = find_monitor_extremes(monitors)
   monitor_ratio = float(monitor_height) / float(monitor_width)

   # Find the input limiting factors
   if output_width is None:
      limiting_factor = 'HEIGHT'
      scale_factor = float(output_height) / float(monitor_height)
      output_width = int(monitor_width * scale_factor)
   elif output_height is None:
      limiting_factor = 'WIDTH'
      scale_factor = float(output_width) / float(monitor_width)
      output_height = int(monitor_height * scale_factor)
   else:
      # We have to fit in a specified width and height
      output_ratio = float(output_height) / float(output_width)
      if (output_ratio < monitor_ratio):
         limiting_factor = 'HEIGHT'
         scale_factor = float(output_height) / float(monitor_height)
      else:
         limiting_factor = 'WIDTH'
         scale_factor = float(output_width) / float(monitor_width)

   if output_ratio is None:
      output_ratio = float(output_height) / float(output_width)

   ret = {"output_width": output_width,
          "output_height": output_height,
          "monitor_width": monitor_width,
          "monitor_height": monitor_height,
          "scale_factor": scale_factor,
          "limiting_factor": limiting_factor,
          "monitor_ratio": monitor_ratio,
          "output_ratio": output_ratio}
   log_debug("Using scale of:", ret)
   return ret

def pixel_to_terminal(layout, pixel_location,
                      term_offset=None, pixel_offset=None):
   """Convert pixels to terminal locations.  Apply pixel_offset
      before conversion and term_offset (terminal_offset) after
      conversion."""
   pixel_x, pixel_y = pixel_location

   # Apply pixel offset
   if pixel_offset is not None:
      pixel_x += pixel_offset[0]
      pixel_y += pixel_offset[1]

   # Subtrace 1 to bump everything down into lower cell
   term_x = int((pixel_x - 1) * layout['scale_factor'])
   term_y = int(((pixel_y - 1) * layout['scale_factor']) / MONITOR_SCALE)

   # Apply terminal offset
   if term_offset is not None:
      term_x += term_offset[0]
      term_y += term_offset[1]

   log_debug(pixel_location, "becomes", [term_x, term_y],
             "with term_offset", term_offset,
             "and pixel_offset", pixel_offset,
             "using scale factor of", layout['scale_factor'])

   # Keep things in check.  This can crop things slightly but fixes
   # small rounding errors.
   if term_x >= layout['output_width']:
      term_x = layout['output_width'] - 1

   if term_y >= int(layout['output_height'] / MONITOR_SCALE):
      term_y = int((layout['output_height'] / MONITOR_SCALE) - 1)

   return [term_x, term_y]

def add_horiz_line(v_buf, v_1, v_2, arrows=False, title=None):
   """Draw a horizonal line from v_1 to v_2 in v_buf.  Turn it into
      an arrow if arrows is True.  Add a title on the line if title
      is given."""
   # Horizontal line has same Y component
   log_debug("Drawing horiz line from", v_1, "to", v_2)
   assert v_1[1] == v_2[1]
   x_1 = v_1[0]
   x_2 = v_2[0]
   y = v_1[1]

   v_buf[x_1][y] = '+'
   v_buf[x_2][y] = '+'
   if x_1 > x_2:
      t = x_2
      x_2 = x_1
      x_1 = t

   text = {}
   if title is not None:
      center = x_2 - x_1
      center_with_offset = int((center - len(title)) / 2)
      for x in range(0, len(title)):
         text[center_with_offset + x] = title[x]

   for x in range(x_1+1, x_2):
      if v_buf[x][y] == '+':
         # Don't draw over other corners
         continue
      try:
         if (x == (x_1 + 1) and arrows):
            v_buf[x][y] = '<'
         elif (x == (x_2 - 1) and arrows):
            v_buf[x][y] = '>'
         elif x in text:
            v_buf[x][y] = text[x]
         else:
            v_buf[x][y] = '-'
      except:
         print("Unable to set[", x, ",", y, "]")
         raise

def add_vert_line(v_buf, v_1, v_2, arrows = False, title=None):
   """Draw a veritcal line from v_1 to v_2 in v_buf.  Turn it into
      an arrow if arrows is True.  Add a title on the line if title
      is given."""
   # I should be able to combine this with the above function but
   # they are not _that_ similar.
   log_debug("Drawing vertical line from", v_1," to", v_2)
   assert v_1[0] == v_2[0]
   y_1 = v_1[1]
   y_2 = v_2[1]
   x = v_1[0]

   v_buf[x][y_1] = '+'
   v_buf[x][y_2] = '+'
   if y_1 > y_2:
      t = y_2
      y_2 = y_1
      y_1 = t

   text = {}
   if title is not None:
      center = y_2 - y_1
      center_with_offset = int((center - len(title)) / 2)
      for y in range(0, len(title)):
         text[center_with_offset + y] = title[y]
   for y in range(y_1+1, y_2):
      if v_buf[x][y] == '+':
         # Don't draw over other corners
         continue
      try:
         if (y == (y_1 + 1) and arrows):
            v_buf[x][y] = '^'
         elif (y == (y_2 - 1) and arrows):
            v_buf[x][y] = 'V'
         elif y in text:
            v_buf[x][y] = text[y]
         else:
            v_buf[x][y] = '|'
      except:
         print("Unable to set[", x, ",", y, "]")
         raise

def add_text(v_buf, monitor, layout, text, location):
   """Add text at location in v_buf providing there is enough room.
      location needs to be in terminal units"""
   required_term_spaces = len(text)
   available_term_spaces = monitor['resolution'][0] * layout['scale_factor']
   log_debug(text,"requires", str(required_term_spaces) + " terminal spaces;",
             available_term_spaces, " terminal spaces available")
   if required_term_spaces <= available_term_spaces:
      for idx, val in enumerate(text):
         v_buf[location[0]+idx][location[1]] = val

def add_overall_pixel_scales(v_buf, layout):
   """This adds axis to our output that shows what the size of the layout is"""
   add_horiz_line(v_buf,
                  [0, len(v_buf[0]) - 1],
                  [len(v_buf) - 1, len(v_buf[0]) - 1],
                  arrows = True,
                  title = str(layout['monitor_width']))
   add_vert_line(v_buf,
                 [len(v_buf) - 1, 0],
                 [len(v_buf) - 1, len(v_buf[0]) - 1],
                 arrows = True,
                 title = str(layout['monitor_height']))

def print_to_vid_buffer(v_buf, layout, monitor, pixel_offset=None):
   """Print the monitor into the v_buf.  Add text about the monitor
      onto the monitor added to the v_buf."""

   # Calculate where all the four corners are in terminal space
   # by translating from pixel space.
   upper_left = pixel_to_terminal(layout,
                                  monitor['upper_left'],
                                  pixel_offset=pixel_offset)
   upper_right = pixel_to_terminal(layout,
                                   [monitor['upper_left'][0] +
                                    monitor['resolution'][0],
                                    monitor['upper_left'][1]],
                                   pixel_offset=pixel_offset)
   lower_left = pixel_to_terminal(layout,
                                  [monitor['upper_left'][0],
                                   monitor['upper_left'][1] +
                                   monitor['resolution'][1]],
                                  pixel_offset=pixel_offset)
   lower_right = pixel_to_terminal(layout,
                                   [monitor['upper_left'][0] +
                                    monitor['resolution'][0],
                                    monitor['upper_left'][1] +
                                    monitor['resolution'][1]],
                                   pixel_offset=pixel_offset)

   # Draw the lines representing the monitor
   add_horiz_line(v_buf, upper_left, upper_right)
   add_horiz_line(v_buf, lower_left, lower_right)
   add_vert_line(v_buf, upper_left, lower_left)
   add_vert_line(v_buf, upper_right, lower_right)

   # Add some monitor descriptions as text
   add_text(v_buf,
            monitor,
            layout,
            monitor['name'],
            pixel_to_terminal(layout,
                              monitor['upper_left'],
                              term_offset=[1,1],
                              pixel_offset=pixel_offset))
   add_text(v_buf,
            monitor,
            layout,
            "{0}x{1}".format(*monitor['resolution']),
            pixel_to_terminal(layout,
                              monitor['upper_left'],
                              term_offset=[1,2],
                              pixel_offset=pixel_offset))

def print_vid_buffer(v_buf):
   """Print the video buffer to the console"""
   columns = len(v_buf)
   rows = len(v_buf[0])
   log_debug("Video buffer is", columns, "columns", rows, "rows")
   for row in range(rows):
      for column in range(columns):
         sys.stdout.write(v_buf[column][row])
      sys.stdout.write('\n')

def display_layout(layout, monitors, left_padding=0, top_padding=0):
   """Print some output of what the monitor layout looks like"""

   # Allocate the Video Buffer.  The output in this case is the terminal.
   vid_buffer = []
   terminal_width = layout['output_width']
   terminal_height = int(layout['output_height'] / MONITOR_SCALE)
   log_debug("Terminal output is:", [terminal_width, terminal_height])


   # I want to be able to address the video buffer in the form of v[x][y],
   # so we need the x to be the columns and the y to be the rows.  This
   # makes for a slightly nonsensical vid_buffer creator.
   #
   # Need to add 1 to the width and height to have room for the axis
   for y in range(terminal_width + 1):
      line = []
      for x in range(terminal_height + 1):
         line.append(' ')
      vid_buffer.append(line)

   # Now that we have a video buffer add all the monitors to it
   for monitor in monitors:
      print_to_vid_buffer(vid_buffer, layout, monitor,
                          pixel_offset=[left_padding, top_padding])

   # Add the axis
   add_overall_pixel_scales(vid_buffer, layout)
   print_vid_buffer(vid_buffer)

def open_image(image):
   """Open an image at image and return the PIL open version"""
   if not os.path.isfile(image):
      print("Warning:", image, "does not exist.  Skipping...")
      return None
   f = open(image, 'rb')
   return Image.open(f)

def split_images(monitors, opts):
   """Split apart the images"""
   # Main iterator over the supplied image parameters
   for image in opts.img_file:
      if not opts.quiet:
         print("Processing: ", image)
      split_image(monitors, opts, image)

def calculate_padding(monitors, opts, output_layout, img_size):
   """Calculate padding values for the 4 images of the monitors overlayed
      onto the image based off what the user wants done."""

   # Easy reference variables
   img_width, img_height = img_size
   scale_factor = output_layout['scale_factor']

   # How much space is left to play with?
   vert_remainder = int(img_height - (output_layout['monitor_height'] * scale_factor))
   horz_remainder = int(img_width -  (output_layout['monitor_width'] * scale_factor))
   log_debug("vertical_remainder:  ", vert_remainder)
   log_debug("horizontal_remainder:", horz_remainder)

   if opts.left:
      # All pixels from the left!
      left_padding = 0
      right_padding = horz_remainder
   elif opts.right:
      # All pixels from the right!
      left_padding = horz_remainder
      right_padding = 0
   elif opts.left_padding is not None:
      if opts.left_padding <= horz_remainder:
         left_padding = opts.left_padding
         right_padding = horz_remainder - left_padding
      else:
         print("WARNING: left_padding value of", opts.left_padding,
               "> padding pixels of", horz_remainder, "(ignoring)")
         left_padding = int(horz_remainder / 2)
         right_padding = left_padding
   elif opts.right_padding is not None:
      if opts.right_padding <= horz_remainder:
         right_padding = opts.right_padding
         left_padding = horz_remainder - right_padding
      else:
         print("WARNING: right_padding value of", opts.right_padding,
               "> padding pixels of", horz_remainder, "(ignoring)")
         left_padding = int(horz_remainder / 2)
         right_padding = left_padding
   else:
      # Center it
      left_padding = int(horz_remainder / 2)
      right_padding = left_padding

   if opts.top:
      # All pixels from the top!
      top_padding = 0
      bottom_padding = vert_remainder
   elif opts.bottom:
      # All pixels from the bottom!
      top_padding = vert_remainder
      bottom_padding = 0
   elif opts.top_padding is not None:
      if opts.top_padding <= vert_remainder:
         top_padding = opts.top_padding
         bottom_padding = vert_remainder - top_padding
      else:
         print("WARNING: top_padding value of", opts.top_padding,
               "> padding pixels of", vert_remainder, "(ignoring)")
         top_padding = int(vert_remainder / 2)
         bottom_padding = top_padding
   elif opts.bottom_padding is not None:
      if opts.bottom_padding <= vert_remainder:
         bottom_padding = opts.bottom_padding
         top_padding = vert_remainder - bottom_padding
      else:
         print("WARNING: bottom_padding value of", opts.bottom_padding,
               "> padding pixels of", vert_remainder, "(ignoring)")
         top_padding = int(vert_remainder / 2)
         bottom_padding = top_padding
   else:
      #Center it
      top_padding = int(vert_remainder / 2)
      bottom_padding = top_padding

   log_debug("left_padding:", left_padding)
   log_debug("right_padding:", right_padding)
   log_debug("top_padding:", top_padding)
   log_debug("bottom_padding:", bottom_padding)
   return left_padding, right_padding, top_padding, bottom_padding

def show_projection(monitors, output_layout, opts, image,
                    img_width, img_height, left_padding, top_padding):
   """Perform a few atrocities to show the user what the cropping will
      approximately look like"""
   # Make a fake monitor and use it.  Set the overall size of the monitor
   # to the width and height of the background image.  This will generate
   # a scale for us that tells us what scale factor we need to use to display
   # everything on the terminal overlayed on the actual image.
   fake_monitor = [{"name": "Background Image",
                    "resolution": [img_width, img_height],
                    "upper_left": [0,0]}]

   # Subtrack one from the terminal width for axis room.
   layout = calculate_scale(fake_monitor,
                            output_width=get_terminal_width() - 1)

   # Here is the fun part.  We have a scale factor for using with our image
   # but now we want to show that scale factor to the user which means we
   # need to scale our output scale factor by the terminal scale factor to
   # make it display properly on the terminal.
   layout['scale_factor'] = output_layout['scale_factor'] * layout['scale_factor']

   # Our padding is also borked up because we need to handle that MONITOR_SCALE
   # thing.  left and right padding is fine.  Scale the MONITOR_SCALE by
   # the output scale and apply that to the padding.
   top_padding = int(top_padding * (MONITOR_SCALE * output_layout['scale_factor']))
   print("")
   print("Projection of monitor definition file onto", image + ":")
   display_layout(layout, monitors,
                  left_padding=left_padding, top_padding=top_padding)

def split_image(monitors, opts, image):
   """Split apart an individual image"""
   img = open_image(image)
   if img is None:
      # I didn't want to process that image anyway.
      return

   # Figure out how big our image is
   img_width, img_height = img.size

   # Figure out how we have to scale it to fit our monitors onto it
   output_layout = calculate_scale(monitors,
                                   output_width=img_width,
                                   output_height=img_height)

   # Make a short variable so I don't have to type too much
   scale_factor = output_layout['scale_factor']

   # Figure out our padding
   left_padding, _, top_padding, _ = \
      calculate_padding(monitors, opts, output_layout, img.size)

   # Header so debug output is readable
   log_debug("Cropping an image at: [left, upper, right, lower]")
   if not opts.quiet:
      # Show the user what this is going to look like
      show_projection(monitors, output_layout, opts, image, img_width,
                      img_height, left_padding, top_padding)
   for monitor in monitors:
      # Break out each individual monitors crop from the main image.
      left = left_padding + int(monitor['upper_left'][0] * scale_factor)
      upper = top_padding + int(monitor['upper_left'][1] * scale_factor)
      right = left + int(monitor['resolution'][0] * scale_factor)
      lower = upper + int(monitor['resolution'][1] * scale_factor)
      log_debug("Cropping image at:", [left, upper, right, lower],
                "->", (right - left, lower - upper))
      cropped_image = img.crop(box=[left,upper,right,lower])

      # Scale if needed
      if not opts.crop_only:
         # Maybe we got lucky and don't need to do anything
         if monitor['resolution'] != cropped_image.size:
            alg = Image.BICUBIC
            alg_name = "BICUBIC"
            if monitor['resolution'][0] < cropped_image.size[0]:
               # We are shrinking.  ANTIALIAS works better going down
               alg = Image.ANTIALIAS
               alg_name = "ANTIALIAS"
            log_debug("Resizing", cropped_image.size, "image to:",
                      monitor['resolution'], "(" + alg_name + ")")
            resized_image = cropped_image.resize(monitor['resolution'],
                                                 resample=alg)
         else:
            log_debug("Output image already in correct size.  Skipping resize")
            resized_image = cropped_image
      else:
         resized_image = cropped_image
      output_filename = image[:image.rfind('.')] + monitor['suffix'] + \
                        image[image.rfind('.'):]
      log_debug("Writing output to", output_filename)
      resized_image.save(output_filename)


if __name__ == '__main__':
   opts = parse_cmdline()

   # Read the monitors
   monitors = parse_monitor(opts.monitor)

   if not opts.quiet:
      # Show the user the layout if we aren't quiet
      layout = calculate_scale(monitors,
                               output_width=get_terminal_width() - 1)
      print("Monitor Layout read from definition file:")
      display_layout(layout, monitors)

   # Do the work
   split_images(monitors, opts)
