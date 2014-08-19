#!/usr/bin/env python
import sys
from os.path import join, dirname, abspath, isfile
import json
import traceback
import imp
try:
    import IPython
except ImportError:
    pass

RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'

HOST = None
PORT = None

def generate_new_flag():
    import string, random
    FLAG_POSSIBILITIES = string.ascii_uppercase + string.digits + string.ascii_lowercase
    new_flag = ''.join(random.choice(FLAG_POSSIBILITIES) for x in range(13))
    return "FLG" + new_flag

def test_benign(benign_fp):
    try:
        benign = imp.load_source('benign', benign_fp)
        from benign import Benign
        print 'Benign..'
        b = Benign()
        b.execute(HOST, PORT, '', '')
        res = b.result()
        print 'Result: %s' % str(res)
        assert res['ERROR'] == 0
    except AssertionError:
        print 'AssertionError while executing Benign'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)
    except Exception:
        print 'Exception while executing Benign'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)

def test_setflag(setflag_fp, flag):
    try:
        setflag = imp.load_source('setflag', setflag_fp)
        from setflag import SetFlag
        print 'SetFlag..'
        sf = SetFlag()
        sf.execute(HOST, PORT, flag)
        res = sf.result()
        print 'Result: %s' % str(res)
        flag_id = res['FLAG_ID']
        token = res['TOKEN']
        assert res['ERROR'] == 0
        return flag_id, token
    except AssertionError:
        print 'AssertionError while executing Setflag'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)
    except Exception:
        print 'Exception while executing Setflag'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)

def test_getflag(getflag_fp, flag_id, token, flag):
    try:
        getflag = imp.load_source('getflag', getflag_fp)
        from getflag import GetFlag
        print 'GetFlag..'
        cf = GetFlag()
        cf.execute(HOST, PORT, flag_id, token)
        res = cf.result()
        print 'Result: %s' % str(res)
        assert res['ERROR'] == 0
        assert res['FLAG'] == flag
    except AssertionError:
        print 'AssertionError while executing Getflag'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)
    except Exception:
        print 'Exception while executing Getflag'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)

def test_exploit(exploit_fp, flag_id, flag):
    try:
        exploit = imp.load_source('exploit', exploit_fp)
        from exploit import Exploit
        print 'Exploit..'
        e = Exploit()
        e.execute(HOST, PORT, flag_id)
        res = e.result()
        print 'Result: %s' % str(res)
        assert res['ERROR'] == 0
        assert res['FLAG'] == flag
    except AssertionError:
        print 'AssertionError while executing Exploit'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)
    except Exception:
        print 'Exception while executing Exploit'
        print traceback.format_exc()
        print '----------------------'
        print RED + 'ERROR' + ENDC
        sys.exit(2)

def test_all_scripts(info_fp, remote_ip):
    info_fp = abspath(info_fp)
    info_dir = dirname(info_fp)
    info = json.load(open(info_fp))

    # FIXME: this is ugly as shit
    global HOST, PORT
    HOST = remote_ip
    PORT = info['port']

    benign_fps = map(lambda fp:join(info_dir, fp), info['benign'])
    exploit_fps = map(lambda fp:join(info_dir, fp), info['exploit'])
    getflag_fp = join(info_dir, info['getflag'])
    setflag_fp = join(info_dir, info['setflag'])

    flag = generate_new_flag()
    for benign_fp in benign_fps:
        test_benign(benign_fp)
    flag_id, token = test_setflag(setflag_fp, flag)
    test_getflag(getflag_fp, flag_id, token, flag)
    for exploit_fp in exploit_fps:
        test_exploit(exploit_fp, flag_id, flag)

    flag2 = generate_new_flag()
    flag_id2, token2 = test_setflag(setflag_fp, flag2)
    for benign_fp in benign_fps:
        test_benign(benign_fp)
    for exploit_fp in exploit_fps:
        test_exploit(exploit_fp, flag_id2, flag2)
    for benign_fp in benign_fps:
        test_benign(benign_fp)
    test_getflag(getflag_fp, flag_id2, token2, flag2)


# This throws an exception if the json is NOT valid.
def check_info_file(info_fp):

    if not isfile(info_fp):
        raise Exception('%s doesn\'t exist.' % info_fp)

    info = json.load(open(info_fp))

    fields = ['name', 'authors', 'port', 'getflag', 'setflag', 'benign',
              'exploit', 'is_working', 'flag_id_description', 'service_description']
    for f in fields:
        if f not in info.keys():
            raise Exception('Field "%s" not found.' % f)

    assert info['name'] != ''
    assert type(info['authors']) == list and len(info['authors']) > 0
    assert type(info['port']) == int
    assert type(info['getflag']) != list and info['getflag'] != ''
    assert type(info['setflag']) != list and info['setflag'] != ''
    assert type(info['benign']) == list and len(info['benign']) > 0
    assert type(info['exploit']) == list and len(info['exploit']) > 0
    assert type(info['is_working']) == int and info['is_working'] in [0, 1]
    assert info['flag_id_description'] != ''
    assert info['service_description'] != ''


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s <info.json> [<remote_ip>]' % sys.argv[0]
        sys.exit(1)

    info_fp = abspath(sys.argv[1])
    try:
        remote_ip = sys.argv[2]
    except IndexError:
        remote_ip = '127.0.0.1'

    check_info_file(info_fp)

    test_all_scripts(info_fp, remote_ip)

    print GREEN + 'SUCCESS' + ENDC
    sys.exit(0)

