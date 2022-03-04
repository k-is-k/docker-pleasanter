import os
from glob import glob


def get_latest_modified_file_path(dirname):
  target = os.path.join(dirname, '*')
  files = [(f, os.path.getctime(f)) for f in glob(target)]
  latest_modified_file_path = sorted(files, key=lambda files: files[1])[-1]
  return latest_modified_file_path[0]


if __name__ == '__main__':
  dirname = "D:/wsl_docker/pleasanter/data/db-backup/dumpall/"
  dirname = get_latest_modified_file_path(dirname)
  print(get_latest_modified_file_path(dirname))