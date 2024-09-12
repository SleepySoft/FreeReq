import os
import re
import fnmatch
from typing import List
from plugin.TestcaseIndexer.TestcaseScannerBase import TestcaseScannerBase


class TestcaseFileNameScanner(TestcaseScannerBase):
    def __init__(self, scan_path: str, patterns: List[str]):
        super(TestcaseFileNameScanner, self).__init__(scan_path, patterns)
        self.req_id_file_mapping = {}
        self.testcase_files = []

    def do_scan(self):
        """
        Scan files by specified ReqID pattern. You can scan file name or file content.
        :return:
        """
        req_id_file_mapping = {}
        regex_search = [re.compile(pattern) for pattern in self.scan_patterns]
        regex_extract = [re.compile(f'({pattern})') for pattern in self.scan_patterns]

        for root, dirs, files in os.walk(self.scan_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                self.testcase_files.append(file_path)
                for regex_s, regex_e in zip(regex_search, regex_extract):
                    if regex_s.search(file_name):
                        # Extract the ReqID from the filename
                        req_id = self._extract_req_id_from_filename(file_name, regex_e)
                        if req_id:
                            if req_id in req_id_file_mapping:
                                req_id_file_mapping[req_id].append(file_path)
                            else:
                                req_id_file_mapping[req_id] = [file_path]
        self.req_id_file_mapping = req_id_file_mapping

    def _extract_req_id_from_filename(self, filename, regex):
        """
        Extract the ReqID from the filename based on the pattern.
        :param filename: The name of the file.
        :param regex: The compiled regular expression object.
        :return: The extracted ReqID or None if not found.
        """
        match = regex.search(filename)
        if match:
            try:
                return match.group(1)  # Adjust the group index as needed
            except IndexError:
                print("No such group in the regex pattern.")
                return None
        else:
            return None

    def get_mapping(self) -> dict:
        return self.req_id_file_mapping

    def testcase_count(self) -> int:
        return len(self.testcase_files)
