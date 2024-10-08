import os
import shutil
import datetime
import platform
from sys import executable as py_executable
from PyInstaller.__main__ import run as py_build_exe


self_path = os.getcwd()
print(self_path)


os.chdir(self_path)
_py_executable_path = os.path.abspath(os.path.dirname(py_executable))


if platform.system() == 'Windows':
    _build_exe_args = (
        '--clean',
        '--noconsole',
        '--i', os.path.join(self_path, 'doc', 'logo.ico'),
        '--paths', self_path,
        '-n', 'FreeReq',
        '-y', os.path.join(self_path, 'FreeReq.py')
    )
else:
    _build_exe_args = (
        '--clean',
        '--i', os.path.join(self_path, 'doc', 'logo.ico'),
        '--paths', self_path,
        '-n', 'FreeReq',
        '-y', os.path.join(self_path, 'FreeReq.py')
    )


def build_exe():
    py_build_exe(pyi_args=_build_exe_args)


def copy_and_log(src: str, dest: str):
    print('Copy file: %s -> %s' % (src, dest))
    shutil.copyfile(src, dest)


def copy2_and_log(src: str, dest: str):
    print('Copy file: %s -> %s' % (src, dest))
    shutil.copy2(src, dest)


def copy_dir_and_log(src: str, dest: str):
    print('Copy folder: %s -> %s' % (src, dest))
    shutil.copytree(src, dest)


def add_extra_files():
    copy_and_log(os.path.join(self_path, 'FreeReq.req'),
                 os.path.join(self_path, 'dist', 'FreeReq', 'FreeReq.req'))
    copy_dir_and_log(os.path.join(self_path, 'res'),
                 os.path.join(self_path, 'dist', 'FreeReq', 'res'))


def __add_dir_in_zip(_zip_f, dir_name, arc_pre_path=''):
    file_list = []
    if arc_pre_path and not arc_pre_path.endswith('/'):
        arc_pre_path = '{}/'.format(arc_pre_path)
    if os.path.isfile(dir_name):
        file_list.append(dir_name)
    else:
        for root, dirs, files in os.walk(dir_name):
            for name in files:
                file_list.append(os.path.join(root, name))
    for file in file_list:
        arc_name = file[len(dir_name):]
        print(arc_name)
        _zip_f.write(file, arc_pre_path + arc_name)


def packing_app(app_pkg_name):
    print('Packing application...')
    if os.path.exists(app_pkg_name):
        os.remove(app_pkg_name)
        print(app_pkg_name, 'is removed')
    from zipfile import ZipFile
    with ZipFile(app_pkg_name, 'w') as zip_f:
        __add_dir_in_zip(zip_f, 'dist/FreeReq', 'FreeReq')


def format_app_package_name():
    # from readme import VERSION as _app_version
    name_format = 'FreeReq-{version}-{os_name}_{os_machine}_{datetime}.zip'
    _os_name = platform.system() + platform.release()
    _os_machine = platform.machine()
    return name_format.format(os_name=_os_name,
                              os_machine=_os_machine,
                              version=1.4,
                              datetime=datetime.datetime.now().strftime('%Y%m%d'))


if __name__ == "__main__":
    try:
        build_exe()
        add_extra_files()
        packing_app(f'dist/{format_app_package_name()}')
    except Exception as exception:
        print('ERROR:', 'Build failed!', exception)
        import traceback
        traceback.print_exc()
        input()
        pass
    pass
