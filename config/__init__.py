from pathlib import Path

from .config_class import Config, config_file

config_pair = {
    Config: config_file,
}

__all__ = [Config]


for i,j in config_pair.items():
    if not Path(j).exists():
        i().to_yaml(yaml_path=j)

