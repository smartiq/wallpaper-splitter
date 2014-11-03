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
   sys.exit("Please install Pillow")

Msg_level = 0
MONITOR_SCALE = 2 # 8x16 for a ``normal'' cursor so use a vertical scale factor
                  # of 2.

def log_debug(*args, **kwds):
   if Msg_level >= 7:
      print(*args, **kwds)

def parse_cmdline():
   """Do command line parsing stuff"""
   parser = argparse.ArgumentParser(description = 'Wallpaper-Splitter')
   parser.add_argument('--monitor', '-m', required=True,
                       metavar='<monitor_def_file.json>',
                       help="Monitor Layout Definition JSON File")
   parser.add_argument('--quiet', '-q', action='store_true',
                       help="Quiet Output")
   parser.add_argument("img_file", nargs='+',
                       help='Image files to convert')
   parser.add_argument("--verbose", '-v', action='store_true',
                       help='Verbose Output')
   args = parser.parse_args()

   if args.verbose:
      global Msg_level
      Msg_level = 7

   log_debug(args)
   return args

def parse_monitor(monitor_file):
   """Make certain the monitors file looks good and return the monitor
      section of it."""
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
   """Return the max width and max height of the monitors"""
   max_width = 0
   max_height = 0
   for monitor in monitors:
      right_edge = monitor["upper_left"][0] + monitor["resolution"][0]
      if right_edge > max_width:
         log_debug("Monitor", monitor["name"], "gives new right edge",
                   right_edge)
         max_width = right_edge
      top_edge = monitor["upper_left"][1] + monitor["resolution"][1]
      if top_edge > max_height:
         log_debug("Monitor", monitor["name"], "gives new height",
                   top_edge)
         max_height = top_edge
   log_debug("Monitor maximums:", [max_width, max_height])
   return max_width, max_height


def calculate_display(scale):
   output_num_cols_pixels = output_width
   output_num_rows_pixels = output_height
   log_debug("Making", output_width, "pixels fit on", output_num_cols_pixels, "columns")


   pix_per_col = int(float(output_width)/float(output_num_cols_pixels))
   log_debug("Using", pix_per_col, "pixels per column")
   # Assume the console is 8x16 character pixels, which means the height
   # is twice the width
   if height_scale is not None and output_height is None:
      pix_per_row = height_scale * pix_per_col
   log_debug("Using", pix_per_row, "pixels per row")
   output_num_rows_pixels = int(float(output_height) / float(pix_per_row))
   log_debug("Using", output_num_rows_pixels, "rows")

def calculate_scale(monitors, output_width=None, output_height=None):
   """Calculate the Desired Monitor Layout.  output_width or output_height
      could be limiting factor."""
   assert output_width is not None or output_height is not None

   # We are either WIDTH or HEIGHT limited
   limiting_factor = None
   output_ratio = None

   # Find the monitor ratio
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

def pixel_to_terminal(layout, pixel_location, offset=None):
   """Convert pixels to terminal locations"""
   pixel_x, pixel_y = pixel_location
   # Subtrace 1 to bump everything down into lower cell
   term_x = int((pixel_x-1) * layout['scale_factor'])
   term_y = int(((pixel_y-1) * layout['scale_factor']) / MONITOR_SCALE)

   if offset is not None:
      term_x += offset[0]
      term_y += offset[1]

   log_debug(pixel_location, "becomes", [term_x, term_y], "with offset", offset)

   # Keep things in check
   if term_x >= layout['output_width']:
      term_x = layout['output_width'] - 1

   if term_y >= int(layout['output_height'] / MONITOR_SCALE):
      term_y = int((layout['output_height'] / MONITOR_SCALE) - 1)

   return [term_x, term_y]

def add_horiz_line(v_buf, v_1, v_2):
   """Draw a horizonal line from v_1 to v_2 in v_buf"""
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

   for x in range(x_1+1, x_2):
      if v_buf[x][y] == '+':
         continue
      try:
         v_buf[x][y] = '-'
      except:
         print("Unable to set[", x, ",", y, "]")
         raise

def add_vert_line(v_buf, v_1, v_2):
   """Draw a veritcal line from v_1 to v_2 in v_buf"""
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

   for y in range(y_1+1, y_2):
      if v_buf[x][y] == '+':
         continue
      try:
         v_buf[x][y] = '|'
      except:
         print("Unable to set[", x, ",", y, "]")
         raise

def add_text(v_buf, text, location):
   for idx, val in enumerate(text):
      v_buf[location[0]+idx][location[1]] = val


def print_to_vid_buffer(v_buf, layout, monitor):
   """Print the monitor into the v_buf"""
   upper_left = pixel_to_terminal(layout,
                                  monitor['upper_left'])
   upper_right = pixel_to_terminal(layout,
                                   [monitor['upper_left'][0] +
                                    monitor['resolution'][0],
                                    monitor['upper_left'][1]])
   lower_left = pixel_to_terminal(layout,
                                  [monitor['upper_left'][0],
                                   monitor['upper_left'][1] +
                                   monitor['resolution'][1]])
   lower_right = pixel_to_terminal(layout,
                                   [monitor['upper_left'][0] +
                                    monitor['resolution'][0],
                                    monitor['upper_left'][1] +
                                    monitor['resolution'][1]])
   add_horiz_line(v_buf, upper_left, upper_right)
   add_horiz_line(v_buf, lower_left, lower_right)
   add_vert_line(v_buf, upper_left, lower_left)
   add_vert_line(v_buf, upper_right, lower_right)
   add_text(v_buf, monitor['name'], pixel_to_terminal(layout,
                                                      monitor['upper_left'],
                                                      offset=[1,1]))

def print_vid_buffer(v_buf):
   """Print the video buffer to the console"""
   columns = len(v_buf)
   rows = len(v_buf[0])
   log_debug("Video buffer is", columns, "columns", rows, "rows")
   for row in range(rows):
      for column in range(columns):
         sys.stdout.write(v_buf[column][row])
      sys.stdout.write('\n')

def display_layout(layout, monitors):
   """Print some output of what the monitor layout looks like"""

   # Allocate the Video Buffer
   vid_buffer = []
   terminal_width = layout['output_width']
   terminal_height = int(layout['output_height'] / MONITOR_SCALE)
   log_debug("Terminal output is:", [terminal_width, terminal_height])
   for y in range(terminal_width):
      line = []
      for x in range(terminal_height):
         line.append(' ')
      vid_buffer.append(line)
   for monitor in monitors:
      print_to_vid_buffer(vid_buffer, layout, monitor)

   print("Approximate Layout:")
   print_vid_buffer(vid_buffer)

def open_image(image):
   if not os.path.isfile(image):
      print("Warning:", image, "does not exist.  Skipping...")
      return None
   f = open(image, 'rb')
   return Image.open(f)

def split_images(monitors, opts):
   """Split apart the images"""
   for image in opts.img_file:
      print("Processing: ", image)
      split_image(monitors, opts, image)

def split_image(monitors, opts, image):
   """Split apart an individual image"""
   img = open_image(image)
   if img is None:
      return

   img_width, img_height = img.size
   output_layout = calculate_scale(monitors,
                                   output_width=img_width,
                                   output_height=img_height)
   scale_factor = output_layout['scale_factor']
   left_padding = int((img_width - (output_layout['monitor_width'] * scale_factor)) / 2)
   top_padding = int((img_height - (output_layout['monitor_height'] * scale_factor)) / 2)
   log_debug("left_padding:", left_padding)
   log_debug("top_padding:", top_padding)

   log_debug("Cropping an image at: [left, upper, right, lower]")
   for monitor in monitors:
      left = left_padding + int(monitor['upper_left'][0] * scale_factor)
      upper = top_padding + int(monitor['upper_left'][1] * scale_factor)
      right = left + int(monitor['resolution'][0] * scale_factor)
      lower = upper + int(monitor['resolution'][1] * scale_factor)
      log_debug("Cropping image at:", [left, upper, right, lower],
                "->", (right - left, lower - upper))
      cropped_image = img.crop(box=[left,upper,right,lower])
      log_debug("Resizing image to:", monitor['resolution'])
      resized_image = cropped_image.resize(monitor['resolution'],
                                           resample=Image.BICUBIC)
      output_filename = image[:image.rfind('.')] + monitor['suffix'] + \
                        image[image.rfind('.'):]
      log_debug("Writing output to", output_filename)
      with open(output_filename, 'wb') as f:
         resized_image.save(f)


if __name__ == '__main__':
   opts = parse_cmdline()
   monitors = parse_monitor(opts.monitor)
   if not opts.quiet:
      layout = calculate_scale(monitors,
                               output_width=get_terminal_width())
      display_layout(layout, monitors)

   split_images(monitors, opts)
