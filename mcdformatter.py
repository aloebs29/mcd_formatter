import sys
import click
import numpy
import imageio

@click.command()
@click.option(
    '--input_filename',
    type=click.Path(exists=True),
    help='File from which the image or comma-separated data will be read.',
)
@click.option(
    '--output_filename',
    type=click.Path(),
    help='File to which the image or comma-separated data will be written.',
)
@click.option(
    '--pack/--unpack',
    '-p/-u',
    help='Whether you want to pack an image into a comma-separated byte string, or unpack an image from a comma-separated byte string.'
)
@click.option(
    '--width',
    '-w',
    default=128,
    help='The width of the output image when unpacking from commma-separated byte string. Default 128.'
)

def mcd_formatter(pack, input_filename, output_filename, width):
  if pack:
    pack_bytestring(input_filename, output_filename)
  else:
    unpack_bytestring(input_filename, output_filename, width)

def pack_bytestring(input_filename, output_filename):
  if input_filename:
    # Make an array representing individual bits
    rawdata = imageio.imread(input_filename)
    bitdata = numpy.vectorize(byteToInvertedBit)(rawdata)

    # Pack bit data into bytes
    bytedata = numpy.zeros([(bitdata.shape[0] * bitdata.shape[1]) // 8], dtype=numpy.uint8)
    for i in range(bitdata.shape[0]):
      for j in range(bitdata.shape[1]):
        index = j + (bitdata.shape[1] * (i // 8))
        bytedata[index] = bytedata[index] | (bitdata[i, j] << (i % 8))

    # Format as comma-separated string (makes it easy for pasting into an array definition)
    output_string = ''.join('0x{:02X}, '.format(a) for a in bytedata)[:-2]
    if output_filename:
      # Write out to file
      with open(output_filename, mode='w') as outfile:
        outfile.write(output_string)
    else:
      # Just print
      print(output_string)

  else:
    click.echo('Must provide --input_filename argument. Type --help for more information.')

def byteToInvertedBit(x):
  if x == 0:
    return 1
  else:
    return 0

def unpack_bytestring(input_filename, output_filename, width):
  if input_filename and output_filename:
    with open(input_filename, mode="r") as text:
      # Convert from comma-separated string to integer array
      bytedata = [int(x.strip(), 16) for x in text.read().split(',')]

      # Parse byte data into 2-d pixel array
      height = (len(bytedata) // width) * 8
      imagedata = numpy.empty([height, width], dtype=numpy.uint8)
      for i, byte in enumerate(bytedata):
        for j in range(8):
          imagedata[((i // width) * 8) + j, (i % width)] = ((byte >> j) & 1) * 255

      # Write to file
      imageio.imwrite(output_filename, imagedata)

  else:
    click.echo('Must provide --input_filename and --output_filename arguments. Type --help for more information.')

if __name__ == "__main__":
  mcd_formatter() # pylint: disable=no-value-for-parameter