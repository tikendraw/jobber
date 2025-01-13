# tests/core/utils/test_file_utils.py
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

import pytest

from v2.core.utils.file_utils import (
    read_json,
    read_jsonl,
    save_file,
    save_json,
)

class TestFileUtils(TestCase):
    def setUp(self):
       self.temp_file = NamedTemporaryFile(delete=False, mode='w+')
       self.temp_file_path = Path(self.temp_file.name)

    def tearDown(self):
       os.unlink(self.temp_file_path)

    def test_save_json_dict(self):
      
        test_data = {"key": "value", "number": 123}
        save_json(test_data, self.temp_file_path)
        
        with open(self.temp_file_path, 'r') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, test_data)

    def test_save_json_list_of_dicts(self):
        test_data = [
            {"key1": "value1", "number1": 1},
            {"key2": "value2", "number2": 2},
        ]
        save_json(test_data, self.temp_file_path)

        with open(self.temp_file_path, 'r') as f:
            loaded_data = json.loads(f.read().strip())
            
        self.assertEqual(loaded_data, test_data)

    def test_save_json_invalid_input(self):
        with self.assertRaises(ValueError):
            save_json("not a dict or list", self.temp_file_path)
    
    def test_read_json_success(self):
      test_data = {"key": "value", "number": 123}
      with open(self.temp_file_path, 'w') as f:
          json.dump(test_data, f)

      loaded_data = read_json(self.temp_file_path.as_posix())
      self.assertEqual(loaded_data, test_data)

    def test_read_json_file_not_found(self):
       loaded_data = read_json('non_exisitent_file')
       self.assertIsNone(loaded_data)

    def test_read_json_invalid_json(self):
       with open(self.temp_file_path, 'w') as f:
          f.write('{"key": "value", "number": 123')
       loaded_data = read_json(self.temp_file_path.as_posix())
       self.assertIsNone(loaded_data)
       
    def test_read_jsonl_success(self):
       test_data = [
            {"key1": "value1", "number1": 1},
            {"key2": "value2", "number2": 2},
        ]
       with open(self.temp_file_path, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
       
       loaded_data = read_jsonl(self.temp_file_path.as_posix())
       self.assertEqual(loaded_data, test_data)

    def test_read_jsonl_file_not_found(self):
       loaded_data = read_jsonl('non_exisitent_file.jsonl')
       self.assertEqual(loaded_data, [])

    def test_read_jsonl_invalid_jsonl(self):
       with open(self.temp_file_path, 'w') as f:
          f.write('{"key": "value", "number": 123\n')
          f.write('invalid json')
       loaded_data = read_jsonl(self.temp_file_path.as_posix())
       self.assertEqual(loaded_data, [])
    
    def test_save_file_str_path(self):
      test_content = 'test_string'
      save_file(test_content, self.temp_file_path.as_posix())

      with open(self.temp_file_path, 'r') as f:
        loaded_content = f.read()
      
      self.assertEqual(test_content, loaded_content)
    
    def test_save_file_path_object(self):
      test_content = 'test_string_object_path'
      save_file(test_content, self.temp_file_path)

      with open(self.temp_file_path, 'r') as f:
        loaded_content = f.read()
      
      self.assertEqual(test_content, loaded_content)
