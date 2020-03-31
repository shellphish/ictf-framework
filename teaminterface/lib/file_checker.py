from base64 import b64decode
from StringIO import StringIO
from tarfile import TarFile
from gzip import GzipFile
from PIL import Image
import struct
import json

def b64_tgz(buf):
    try:
        raw_data = b64decode(buf)
        sio = StringIO(raw_data)
        gzf = GzipFile(fileobj=sio)
        tar = TarFile(fileobj=gzf)
        return buf
    except:
        raise TypeError("Data must be base64-encoded gzipped tar archive")


def get_image_info(data):
    if is_png(data):
        w, h = struct.unpack('>LL', data[16:24])
        width = int(w)
        height = int(h)
    else:
        raise Exception('not a png image')
    return width, height


def is_png(data):
    return data[:8] == '\211PNG\r\n\032\n'and (data[12:16] == 'IHDR')


def b64_png(buf):
    try:
        raw_data = b64decode(buf)
        assert get_image_info(raw_data) == (256, 256)
    except:
        raise TypeError("Image must be a 256x256 PNG.  When calling the API without the Python client, this file must be base64-encoded.")
    return buf


def metadata_dict(buf):
    try:
        m = json.loads(buf)
        print m
        for k, v in m.items():
            if v.strip() == "":
                raise TypeError("You must answer question with ID " + k)
    except TypeError:
        raise
    except:
        raise TypeError("You must answer the metadata questions!")
    return buf
