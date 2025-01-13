# tests/config/test_base_config.py
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional
from unittest import TestCase

import pytest
from pydantic import BaseModel, Field, ValidationError

from v2.config.base_config import YAMLConfigModel, get_base_config


class TestConfig(YAMLConfigModel):
    """A test config model"""
    name: str = Field(default='test')
    value: int = Field(default=100)
    optional: Optional[str] = None
    
class TestConfigWithDefault(YAMLConfigModel):
    """Test config model for defaults"""
    a: int = 1
    b: str = "hello"
    
class TestYAMLConfigModel(TestCase):
    def setUp(self):
        self.temp_yaml_file = NamedTemporaryFile(suffix='.yaml', mode='w+', delete=False)
        self.temp_yaml_path = Path(self.temp_yaml_file.name)
    
    def tearDown(self):
        os.unlink(self.temp_yaml_path)

    def test_from_yaml_valid_data(self):
        self.temp_yaml_file.write("""
            name: 'myconfig'
            value: 200
        """)
        self.temp_yaml_file.flush()

        config = TestConfig.from_yaml(self.temp_yaml_path)

        self.assertEqual(config.name, 'myconfig')
        self.assertEqual(config.value, 200)
        self.assertIsNone(config.optional)
    
    def test_from_yaml_optional_field(self):
        self.temp_yaml_file.write("""
            name: 'myconfig'
            value: 200
            optional: 'optional field'
        """)
        self.temp_yaml_file.flush()
        
        config = TestConfig.from_yaml(self.temp_yaml_path)
        
        self.assertEqual(config.name, 'myconfig')
        self.assertEqual(config.value, 200)
        self.assertEqual(config.optional, 'optional field')

    def test_from_yaml_invalid_data(self):
        self.temp_yaml_file.write("""
            name: 123
            value: "abc"
        """)
        self.temp_yaml_file.flush()
        
        with self.assertRaises(ValidationError):
           TestConfig.from_yaml(self.temp_yaml_path)

    def test_to_yaml(self):
        config = TestConfig(name='mytest', value=300, optional='extra field')
        config.to_yaml(self.temp_yaml_path)

        with open(self.temp_yaml_path, 'r') as f:
            yaml_content = f.read()
        
        # Compare the content, ignoring ordering, white-spaces 
        assert "name: mytest" in yaml_content
        assert "value: 300" in yaml_content
        assert "optional: extra field" in yaml_content
    
    def test_get_base_config_new_file(self):
        # Create a temp file that will be deleted after the test
        temp_file_path = Path(self.temp_yaml_path)

        #write something to it
        config_default = TestConfigWithDefault()
        config_default.to_yaml(temp_file_path)

        # Run the get_base_config function for the first time
        config, created = get_base_config(temp_file_path.as_posix(), output_cls=TestConfigWithDefault)

        # Assert that the function returned a new config and created a new file
        assert created is False
        assert isinstance(config, TestConfigWithDefault)
        assert config.a == 1
        assert config.b == 'hello'
        assert os.path.exists(temp_file_path)

        # Open and assert the file content
        with open(temp_file_path, 'r') as f:
            file_content = f.read()

        assert "a: 1" in file_content
        assert "b: hello" in file_content

    def test_get_base_config_existing_file(self):
        # First, create the config file and write default data in it.
        config_default = TestConfigWithDefault()
        config_default.to_yaml(self.temp_yaml_path)


        # Now, modify the temp file (as if someone had changed it)
        with open(self.temp_yaml_path, 'w') as f:
            f.write("""
            a: 200
            b: 'world'
            """)
        self.temp_yaml_file.flush()
    
        # Call get_base_config again (should load from the existing)
        config2, created2 = get_base_config(filename=self.temp_yaml_path.as_posix(), output_cls=TestConfigWithDefault)
        assert created2 is False
        assert isinstance(config2, TestConfigWithDefault)
        assert config2.a == 200
        assert config2.b == 'world'

    def test_get_base_config_existing_invalid_file(self):
        # First, create the config file and add invalid data
        with open(self.temp_yaml_path, 'w') as f:
            f.write("""
                a: 'test'
                b: 123
            """)
        self.temp_yaml_file.flush()
        
        # Now, call get_base_config with that file, this should recreate the default config
        config, created = get_base_config(self.temp_yaml_path.as_posix(), TestConfigWithDefault)
        
        assert created == True
        assert isinstance(config, TestConfigWithDefault)
        assert config.a == 1
        assert config.b == 'hello'
        
        #verify the content of file
        with open(self.temp_yaml_path, 'r') as f:
            file_content = f.read()
            
        assert "a: 1" in file_content
        assert "b: hello" in file_content