import json
import traceback


import json
from typing import Any

class EasyConfig:
    def __init__(self, config_file: str = 'config.json', key_splitter: str = '.'):
        self.config_file = config_file
        self.key_splitter = key_splitter
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

    def set(self, key: str, value: Any) -> bool:
        keys = key.split(self.key_splitter)
        d = self.config
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            elif not isinstance(d[k], dict):
                return False
            d = d[k]
        d[keys[-1]] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        return True

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(self.key_splitter)
        d = self.config
        for k in keys[:-1]:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        if not isinstance(d, dict) or keys[-1] not in d:
            return default
        return d[keys[-1]]

    def clear(self):
        self.config = {}
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)


# ---------------------------------------------------------------------------------------------------------------------

def test_easy_config():
    config = EasyConfig('config_test.json')
    config.clear()
    assert config.set('a.b.c', 1)
    assert config.get('a.b.c') == 1
    assert config.get('a.b') == {'c': 1}
    assert config.set('a.b', 2)
    assert config.get('a.b') == 2
    assert config.get('a.b.d', 'default') == 'default'
    assert config.set('a.e.f.g', [1, 2, 3])
    assert config.get('a.e.f.g') == [1, 2, 3]

    # Test key not exist
    assert config.get('x.y.z', 'default') == 'default'

    # Test key target is not dict
    assert config.set('a.b.c.d', 2) == False

    print("All tests passed!")


def main():
    test_easy_config()


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
