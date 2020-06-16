import sys
import click
import numpy
import imageio
import textwrap
import re
import os

INVERT = False
OUTPUT_MAX_WIDTH = 120
TAB_WIDTH = 4 # this is subtracted from max width

@click.command()
@click.option(
    '--input_filename',
    type=click.Path(exists=True),
    help='File from which the image or array definition will be read.',
)
@click.option(
    '--pack/--unpack',
    '-p/-u',
    help='Whether you want to pack an image into an array definition, or unpack an image from an array definition.'
)
@click.option(
    '--width',
    '-w',
    default=128,
    help='The width of the output image when unpacking from array definition. Default 128.'
)

def mcd_formatter(pack, input_filename, width):
  if pack:
    pack_bytestring(input_filename)
  else:
    unpack_bytestring(input_filename, width)

def pack_bytestring(input_filename):
  if input_filename:
    # Make an array representing individual bits
    rawdata = imageio.imread(input_filename, pilmode="L")
    bitdata = numpy.vectorize(byte_to_bit)(rawdata)
    # Pack bit data into bytes
    bytedata = numpy.zeros([(bitdata.shape[0] * bitdata.shape[1]) // 8], dtype=numpy.uint8)
    for i in range(bitdata.shape[0]):
      for j in range(bitdata.shape[1]):
        index = j + (bitdata.shape[1] * (i // 8))
        bytedata[index] = bytedata[index] | (bitdata[i, j] << (i % 8))

    # Sanitize input filename as variable name
    var_name = str_to_var_name(os.path.splitext(os.path.basename(input_filename))[0])
    # Format as comma-separated string
    csv_string = ''.join('0x{:02X}, '.format(a) for a in bytedata)[:-2]
    # Create const array declaration
    output_string = format_const_arr(var_name, csv_string, len(bytedata))
    # Write out to file
    with open(f'{os.path.splitext(input_filename)[0]}.txt', mode='w') as outfile:
      outfile.write(output_string)

  else:
    click.echo('Must provide --input_filename argument. Type --help for more information.')

def byte_to_bit(x):
  if INVERT:
    return 1 if x == 0 else 0
  else:
    return 0 if x == 0 else 1

def format_const_arr(var_name, csv_string, arr_len):
  # Create declaration
  output = f'static const uint8_t {var_name}[{arr_len}] = {{\n'

  # Format string to be placed as initialization value
  wrapped = textwrap.fill(csv_string, width=(OUTPUT_MAX_WIDTH - TAB_WIDTH))
  output = output + textwrap.indent(wrapped, "\t")

  # Return with end brace and semicolon
  return output + "\n};\n"

def str_to_var_name(string):
  # See: https://stackoverflow.com/a/3305731
  return re.sub('\W+|^(?=\d)','_', string) # pylint: disable=anomalous-backslash-in-string

def unpack_bytestring(input_filename, width):
  if input_filename:
    with open(input_filename, mode="r") as text:
      # Figure out left and right index of the values
      raw = text.read()
      l_index = raw.find("0x")
      r_index = raw.rfind("0x") + 4
      # Convert from array declaration to integer array
      bytedata = [int(x.strip(), 16) for x in raw[l_index:r_index].split(',')]

      # Parse byte data into 2-d pixel array
      height = (len(bytedata) // width) * 8
      imagedata = numpy.empty([height, width], dtype=numpy.uint8)
      for i, byte in enumerate(bytedata):
        for j in range(8):
          imagedata[((i // width) * 8) + j, (i % width)] = ((byte >> j) & 1) * 255

      # Write to file
      output_filename = f'{os.path.splitext(input_filename)[0]}.bmp'
      imageio.imwrite(output_filename, imagedata)

  else:
    click.echo('Must provide --input_filename argument. Type --help for more information.')

if __name__ == "__main__":
  mcd_formatter() # pylint: disable=no-value-for-parameter