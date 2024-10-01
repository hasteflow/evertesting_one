import os
import sys

tests_folder_path = os.path.abspath(__name__)
src_folder_path = os.path.abspath(f"{tests_folder_path}/../src")

sys.path.append(src_folder_path)
