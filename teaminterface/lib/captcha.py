import json
import pyfiglet
from passlib.utils import generate_password
import random
from redis import Redis

goodfonts = ['banner',
             'standard',
             'digital',
             'f15_____',
             'banner3',
             'c1______']

def random_font():
    #fonts = pyfiglet.FigletFont().getFonts()
    fonts = goodfonts
    f =  random.choice(fonts)
    print f
    return f



def generate_captcha():
    font = random_font()
    fg = pyfiglet.Figlet(font)
    code = generate_password(8,charset="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    captcha = fg.renderText(code)
    return captcha,code

r = Redis()


def set_captcha(code, data):
    if 'metadata' in data.keys():
        data['metadata'] = json.dumps(data['metadata'])
    r.hmset(code, data)

def get_captcha(code):
    data = r.hgetall(code)
    if 'metadata' in data.keys():
        data['metadata'] = json.loads(data['metadata'])
    r.delete(code)
    return data

if __name__ == '__main__':
    print generate_captcha()[0]
