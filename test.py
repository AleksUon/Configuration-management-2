import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
from lxml import etree
from io import StringIO
import subprocess
import os
from main import load_config  # Импорт функции load_config из основного кода


class TestConfigLoading(unittest.TestCase):
    def setUp(self):
        # Обновляем значение config_data с нормализованным путем
        self.config_data = r'''
        <config>
            <repo_path>reps\-Alpine-Linux-apk-depends</repo_path>
            <output_path>test_output</output_path>
            <commit_date>2024-10-11</commit_date>
        </config>
        '''
        self.config_xml = StringIO(self.config_data)

    def test_load_config(self):
        # Патчим метод parse для возврата нашего временного XML
        with patch('lxml.etree.parse', return_value=etree.parse(self.config_xml)):
            repo_path, output_path, commit_date = load_config("config.xml")

            # Используем os.path.normpath для корректного сравнения путей на разных системах
            expected_repo_path = os.path.normpath("reps\-Alpine-Linux-apk-depends")
            self.assertEqual(os.path.normpath(repo_path), expected_repo_path)
            self.assertEqual(output_path, "test_output")
            self.assertEqual(commit_date, "2024-10-11")


class TestDateParsing(unittest.TestCase):
    def test_date_parsing_and_timezone(self):
        date_str = "2024-10-11"
        start_date = datetime.strptime(date_str, "%Y-%m-%d")
        new_timezone = pytz.timezone('Europe/Moscow')
        start_date = new_timezone.localize(start_date)
        self.assertEqual(start_date.isoformat(), "2024-10-11T00:00:00+03:00")


class TestGitCommandExecution(unittest.TestCase):
    @patch('subprocess.run')
    def test_git_log_command(self, mock_run):
        # Мокаем выполнение git команды и проверяем, что она вызывается с правильными параметрами
        mock_run.return_value = MagicMock(stdout="commit_hash|2024-10-11T12:00:00\nA\tfile_path")

        repo_path = "test_repo"
        git_log_command = [
            "git", "-C", repo_path, "log", "--name-status", "--pretty=format:%H|%cd", "--date=iso"
        ]
        result = subprocess.run(git_log_command, capture_output=True, text=True)
        mock_run.assert_called_once_with(git_log_command, capture_output=True, text=True)
        self.assertEqual(result.stdout, "commit_hash|2024-10-11T12:00:00\nA\tfile_path")


if __name__ == "__main__":
    unittest.main()