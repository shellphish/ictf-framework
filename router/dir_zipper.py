from time import gmtime, strftime
import zipfile
import os
from time import time
from time import sleep

last_name = None
max_ndx_2 = 0
fn_ndx    = 0

def get_new_file_name():
    global last_name
    global fn_ndx

    new_name = str(strftime("%H_%M_%S", gmtime())).strip()

    if last_name is None:
        fn_ndx = 0
        last_name = new_name
        return new_name

    if new_name != last_name:
        fn_ndx = 0
        last_name = new_name
        return new_name

    fn_ndx += 1
    new_name = new_name + '_' + str(fn_ndx)

    return new_name

def get_list_of_file(src_dir, move_dir):
    #global max_ndx
    name_max_ndx = None

    file_list = []
    move_list = []

    for in_file_name in os.listdir(src_dir):
        file_list.append(os.path.join(src_dir, in_file_name))
        move_list.append(os.path.join(move_dir, in_file_name))
        trimmed_str = str(in_file_name[12:]).strip()

        if len(trimmed_str) < 1:
            continue

        ndx = int(trimmed_str)

        #if ndx > max_ndx:
        if name_max_ndx is None or ndx > max_ndx:
            print('Max file is ' + in_file_name)
            max_ndx = ndx
            name_max_ndx = os.path.join(src_dir, in_file_name)

    print(str(file_list))
    print(str(move_list))

    if name_max_ndx is not None:
        print('removing ' + name_max_ndx)
        file_list.remove(name_max_ndx)

    return file_list, move_list

def zip_folder(src_dir, dest_dir, out_file_name, move_dir):
    out_file_name = out_file_name + '.zip'
    out_file_path = os.path.join(dest_dir, out_file_name)
    z = zipfile.ZipFile(out_file_path, 'w')

    file_list, move_dir = get_list_of_file(src_dir, move_dir)

    for in_file_name in file_list:

        z.write(in_file_name)
        print(in_file_name)

    z.close()

    ndx = len(file_list)

    print('len 1 = ' + str(len(file_list)) + ' len 2 = ' + str(len(move_dir)))

    while ndx > 0:
        print('ndx = ' + str(ndx))
        ndx -= 1
        os.rename(file_list[ndx], move_dir[ndx])

def continuous_zipping(src_dir, dest_dir, move_dir, sleep_time):
    while True:
        fname = get_new_file_name()
        start = time()
        zip_folder(src_dir, dest_dir, fname, move_dir)
        end = time()

        nap_time = sleep_time + end - start
        if nap_time > 0:
            sleep(nap_time)

continuous_zipping('tmp', 'dest', 'tmp2', 4)
#get_list_of_file('tmp')
