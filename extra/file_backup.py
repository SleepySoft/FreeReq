import os
import glob
import shutil
import datetime


def backup_file(file_name: str, backup_limit: int):
    # Get the path of the file
    file_path = os.path.abspath(file_name)

    # Get the directory of the file
    file_dir = os.path.dirname(file_path)

    # Create the backup directory if it does not exist
    backup_dir = os.path.join(file_dir, 'backup')
    os.makedirs(backup_dir, exist_ok=True)

    # Get the timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S_%f')[:-3]

    # Get the file extension
    file_ext = os.path.splitext(file_name)[1]

    # Create the backup file name
    backup_file_name = os.path.basename(file_name)
    if file_ext:
        backup_file_name = backup_file_name.replace(file_ext, f'_{timestamp}{file_ext}')
    else:
        backup_file_name = f'{backup_file_name}_{timestamp}'

    # Copy the file to the backup directory
    backup_file_path = os.path.join(backup_dir, backup_file_name)
    shutil.copy2(file_path, backup_file_path)

    # Get the number of backup files
    if file_ext:
        backup_files = glob.glob(
            os.path.join(backup_dir, f'{os.path.basename(file_name).replace(file_ext, "")}_*{file_ext}'))
    else:
        backup_files = glob.glob(os.path.join(backup_dir, f'{os.path.basename(file_name)}_*'))
    num_backup_files = len(backup_files)

    # If the number of backup files is greater than the backup limit, delete the oldest file
    if num_backup_files > backup_limit:
        oldest_file = min(backup_files, key=os.path.getctime)
        os.remove(oldest_file)


def backup_file_safe(file_name: str, backup_limit: int) -> bool:
    try:
        backup_file(file_name, backup_limit)
        return True
    except Exception as e:
        print('Back file error.')
        print(e)
        return False
    finally:
        pass
