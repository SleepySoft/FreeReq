from typing import List


class TestcaseScannerBase:
    def __init__(self, scan_path: str, patterns: List[str]):
        self.scan_path = ''
        self.scan_patterns = []

    def do_scan(self):
        """
        Scan files by specified ReqID pattern. You can scan file name or file content.
        :return:
        """
        pass

    def get_mapping(self) -> dict:
        return {'WHATxxxxxx': ['test_case_file_1.robot', 'test_case_file_path_2.robot']}

    def testcase_count(self) -> int:
        return 0
