import sys
import os

def skip_id3(buffer):
    #http://id3.org/d3v2.3.0
    if buffer[0] == 0x49 and buffer[1] == 0x44 and buffer[2] == 0x33:  #'ID3'
        id3v2_flags = buffer[5]
        footer_size = 10 if (id3v2_flags & 0x10) else 0

        #ID3 size encoding is crazy (7 bits in each of 4 bytes)
        z0 = buffer[6]
        z1 = buffer[7]
        z2 = buffer[8]
        z3 = buffer[9]
        if (z0 & 0x80) == 0 and (z1 & 0x80) == 0 and (z2 & 0x80) == 0 and (z3 & 0x80) == 0:
            tag_size = ((z0 & 0x7f) * 2097152) + ((z1 & 0x7f) * 16384) + ((z2 & 0x7f) * 128) + (z3 & 0x7f)
            return 10 + tag_size + footer_size
    return 0

versions = ['2.5', 'x', '2', '1']
layers = ['x', '3', '2', '1']
bit_rates = {
    'V1Lx' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'V1L1' : [0,32,64,96,128,160,192,224,256,288,320,352,384,416,448],
    'V1L2' : [0,32,48,56, 64, 80, 96,112,128,160,192,224,256,320,384],
    'V1L3' : [0,32,40,48, 56, 64, 80, 96,112,128,160,192,224,256,320],
    'V2Lx' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'V2L1' : [0,32,48,56, 64, 80, 96,112,128,144,160,176,192,224,256],
    'V2L2' : [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160],
    'V2L3' : [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160],
    'VxLx' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'VxL1' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'VxL2' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'VxL3' : [0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
  }
sample_rates = {
    'x':   [    0,     0,     0],
    '1':   [44100, 48000, 32000],
    '2':   [22050, 24000, 16000],
    '2.5': [11025, 12000,  8000]
  }
samples = {
    'x': {
      'x': 0,
      '1': 0,
      '2': 0,
      '3': 0
    },
    '1': { #MPEGv1,     Layers 1,2,3
      'x': 0,
      '1': 384,
      '2': 1152,
      '3': 1152
    },
    '2': { #MPEGv2/2.5, Layers 1,2,3
      'x': 0,
      '1': 384,
      '2': 1152,
      '3': 576
    }
}

def frame_size(samples, layer, bit_rate, sample_rate, paddingBit):
    if layer == 1:
        return (((samples * bit_rate * 125 / sample_rate) + paddingBit * 4)) | 0
    else: #layer 2, 3
        return (((samples * bit_rate * 125) / sample_rate) + paddingBit) | 0

def parse_frame_header(header):
    b1 = header[1]
    b2 = header[2]

    version_bits = (b1 & 0x18) >> 3
    version = versions[version_bits]
    simple_version =  '2' if version == '2.5' else version

    layer_bits = (b1 & 0x06) >> 1
    layer = layers[layer_bits]

    bit_rate_key = 'V{0}L{1}'.format(simple_version, layer)
    bit_rate_index = (b2 & 0xf0) >> 4
    if bit_rate_key in bit_rates:
        bit_rate = bit_rates[bit_rate_key][bit_rate_index]
    else:
        bit_rate = 0

    sample_rate_idx = (b2 & 0x0c) >> 2

    if version in sample_rates:
        sample_rate = sample_rates[version][sample_rate_idx]
    else:
        sample_rate = 0

    sample = samples[simple_version][layer]

    padding_bit = (b2 & 0x02) >> 1
    return {
        'bit_rate': bit_rate,
        'sample_rate': sample_rate,
        'frame_size': frame_size(sample, layer, bit_rate, sample_rate, padding_bit),
        'samples': sample
    }

def estimate_duration(bitRate, offset, filesize):
    kbps = float((bitRate * 1000) / 8)
    datasize = filesize - offset

    return round_duration(datasize / kbps)

def round_duration(duration):
  return round(duration * 1000) / 1000 # round to nearest ms

def mp3_duration(filename, cbr_estimate=False):
    duration = 0
    info = None
    filesize = os.path.getsize(filename)

    with open(filename, 'rb') as f:
        buffer = f.read(100)

        if len(buffer) < 100:
            return 0

        offset = skip_id3([ord(x) for x in buffer])

        while True:
            f.seek(offset)
            buffer = [ord(x) for x in f.read(10)]

            if len(buffer) < 10: return round_duration(duration)

            #Looking for 1111 1111 111 (frame synchronization bits)
            if buffer[0] == 0xff and (buffer[1] & 0xe0) == 0xe0:
                info = parse_frame_header(buffer)
                if info['frame_size'] and info['samples']:
                    offset += info['frame_size']
                    duration += ( info['samples'] / float(info['sample_rate']) )
                else:
                    offset+=1 #Corrupt file?
            elif buffer[0] == 0x54 and buffer[1] == 0x41 and buffer[2] == 0x47: #TAG'
                offset += 128; #Skip over id3v1 tag size
            else:
                offset+=1 #Corrupt file?

            if cbr_estimate and info:
                return round_duration(estimate_duration(info['bit_rate'], offset, filesize))

    return round_duration(duration)

def usage():
    print '{} [-e] filename'.format(os.path.basename(sys.argv[0]))
    print 'OPTIONS'
    print '-e     Estimate duration. Faster, but inaccurate result'

if __name__ == "__main__":

    if len(sys.argv[1:]) == 1:
        filename = sys.argv[1]
        cbr_estimate = False
    elif len(sys.argv[1:]) == 2:
        if sys.argv[1] == '-e':
            cbr_estimate = True
            filename = sys.argv[2]
        else:
            usage()
            sys.exit(2)
    else:
        usage()
        sys.exit(2)

    print mp3_duration(filename, cbr_estimate)
