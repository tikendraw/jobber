from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class YAMLConfigModel(BaseModel):
    """
    A base Pydantic model with YAML serialization and deserialization capabilities.
    
    Provides methods to:
    - Load configuration from a YAML file
    - Save configuration to a YAML file
    - Validate configuration data
    """
    
    # Pydantic model configuration
    model_config = ConfigDict(
        extra='ignore',  # Ignore extra fields not defined in the model
        populate_by_name=True,  # Allow population by field names
        from_attributes=True  # Allow creating model from object attributes
    )
    
    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> 'YAMLConfigModel':
        """
        Load and parse configuration from a YAML file.
        
        Args:
            yaml_path (Path | str): Path to the YAML configuration file
        
        Returns:
            YAMLConfigModel: Parsed and validated configuration model
        """
        yaml_path = Path(yaml_path)
        
        # Read YAML file
        with yaml_path.open('r') as file:
            config_dict = yaml.safe_load(file)
        
        # Create model instance with validation
        return cls(**config_dict)
    
    def to_yaml(self, yaml_path: Path | str, **dump_kwargs: Any) -> None:
        """
        Save the current configuration to a YAML file.
        
        Args:
            yaml_path (Path | str): Path to save the YAML configuration file
            **dump_kwargs: Additional keyword arguments to pass to yaml.dump()
        """
        yaml_path = Path(yaml_path)
        
        # Default YAML dump parameters with option to override
        default_kwargs = {
            'default_flow_style': False,
            'sort_keys': False,
            'indent': 2
        }
        default_kwargs.update(dump_kwargs)
        
        # Convert model to dictionary and dump to YAML
        with yaml_path.open('w') as file:
            yaml.dump(self.model_dump(), file, **default_kwargs)


