import os
import traceback
import importlib.util
from functools import partial
from inspect import getmembers, isfunction

from typing import List, Union


DEFAULT_PLUGIN_PROB_FUNCTIONS = ['plugin_prob', 'plugin_capacities']


# ----------------------------------------------------------------------------------------------------------------------

class PluginWrapper:
    def __init__(self, plugin_manager, plugin_name: str, module_path: str, module_name: str, module_inst):
        self.plugin_manager = plugin_manager
        self.plugin_name = plugin_name
        self.module_path = module_path
        self.module_name = module_name
        self.module_inst = module_inst
        self.user_data = {}

    def __getattr__(self, attr):
        return partial(self.invoke, attr)

    def invoke(self, _function: str, *args, **kwargs) -> any:
        try:
            func = getattr(self.module_inst, _function)
            return func(*args, **kwargs)
        except Exception as e:
            print('---------------------- Not an issue -----------------------')
            print(f'Invoke error - ${e}')
            print(traceback.format_exc())
            print('-----------------------------------------------------------')
            return None
        finally:
            pass

    def has_function(self, function: str) -> bool:
        try:
            return callable(getattr(self.module_inst, function))
        except Exception as e:
            return False
        finally:
            pass

    def get_attribute(self, attribute: str) -> any:
        try:
            return callable(getattr(self.module_inst, attribute))
        except Exception as e:
            return None
        finally:
            pass


# ----------------------------------------------------------------------------------------------------------------------

class PluginManager:
    def __init__(self, plugin_path: Union[str, List[str]] = '', prob_functions: [str] or None = None):
        self.plugin_path = plugin_path
        self.prob_functions = DEFAULT_PLUGIN_PROB_FUNCTIONS if prob_functions is None else prob_functions
        self.plugins = {}

    def get_plugin(self, plugin_name: str) -> PluginWrapper:
        return self.plugins.get(plugin_name, None)

    def list_plugin(self) -> [str]:
        return [f.removesuffix('.py') for f in self.__list_py_files()]

    def load_plugin(self, plugin_name: str) -> PluginWrapper or None:
        if os.path.isabs(plugin_name):
            file_path = plugin_name
        else:
            file_path = os.path.join(self.plugin_path, plugin_name)
            if not file_path.endswith('.py'):
                file_path += '.py'
        plugin_data = self.__load_plugin_file(file_path)
        self.__check_update_plugins(file_path, plugin_data)
        return plugin_data

    def scan_plugin(self) -> []:
        plugin_list = []
        for py_file in self.__list_py_files():
            plugin_data = self.__load_plugin_file(py_file)
            self.__check_update_plugins(py_file, plugin_data)
            plugin_list.append(plugin_data)
        return plugin_list

    def invoke_one(self, plugin_name: str, function: str, *args, **kwargs) -> any:
        plugin_wrapper = self.__get_plugin_by_name(plugin_name)
        return PluginManager.safe_invoke(plugin_wrapper, function, *args, **kwargs)

    def invoke_all(self, function: str, *args, **kwargs) -> []:
        return [PluginManager.safe_invoke(plugin_wrapper, function, *args, **kwargs)
                for plugin_wrapper in self.plugins.values()]

    @staticmethod
    def plugin_name(plugin_path: str) -> str:
        return os.path.splitext(os.path.basename(plugin_path))[0]

    @staticmethod
    def safe_invoke(plugin_wrapper: PluginWrapper, function: str, *args, **kwargs) -> any:
        try:
            return plugin_wrapper.invoke(function, *args, **kwargs) if plugin_wrapper is not None else None
        except Exception as e:
            print('---------------------- Not an issue -----------------------')
            print("Function run fail.")
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
            print('-----------------------------------------------------------')
        finally:
            pass

    # --------------------------------------------------------------------------------

    def __list_py_files(self) -> []:
        py_files = []
        module_files = os.listdir(self.plugin_path)
        for file_name in module_files:
            if not file_name.endswith('.py') or file_name.startswith('_') or file_name.startswith('.'):
                continue
            py_files.append(os.path.join(self.plugin_path, file_name))
        return py_files

    def __get_plugin_by_name(self, plugin_name: str) -> PluginWrapper or None:
        ensure_plugin_name = PluginManager.plugin_name(plugin_name)
        return self.plugins.get(ensure_plugin_name, None)

    def __check_update_plugins(self, plugin_name: str, plugin_wrapper: PluginWrapper or None):
        ensure_plugin_name = PluginManager.plugin_name(plugin_name)
        if plugin_wrapper is None:
            if ensure_plugin_name in self.plugins.keys():
                del self.plugins[ensure_plugin_name]
        else:
            self.plugins[ensure_plugin_name] = plugin_wrapper

    def __load_plugin_file(self, file_path: str) -> PluginWrapper or None:
        plugin_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if module is None or not self.__check_prob_functions(module):
                raise ValueError('No prob functions.')
            return PluginWrapper(self, plugin_name, file_path, plugin_name, module)
        except Exception as e:
            print('---------------------- Not an issue -----------------------')
            print('When import module: ' + plugin_name)
            print(e)
            print(traceback.format_exc())
            print('Ignore...')
            print('-----------------------------------------------------------')
            return None
        finally:
            pass

    def __check_prob_functions(self, module) -> bool:
        for pf in self.prob_functions:
            if not callable(getattr(module, pf)):
                return False
        return True


# ---------------------------------------------------------------------------------------------------------------------

def main():
    pm1 = PluginManager('plugin_manager_test')
    pm1.scan_plugin()
    print(pm1.plugins)

    assert pm1.invoke_one('plugin_with_prob', 'foo') is None
    assert pm1.invoke_one('plugin_without_prob', 'foo') is None

    assert pm1.invoke_one('plugin_with_prob', 'bar') == 'bar'
    assert pm1.invoke_one('plugin_without_prob', 'bar') is None

    print(pm1.invoke_all('foo'))
    print(pm1.invoke_all('bar'))

    print('-----------------------------------------------------------------------')

    pm2 = PluginManager('plugin_manager_test', [])
    pm2.scan_plugin()
    print(pm2.plugins)

    assert pm2.invoke_one('plugin_with_prob', 'foo') is None
    assert pm2.invoke_one('plugin_without_prob', 'foo') == 'foo'

    assert pm2.invoke_one('plugin_with_prob', 'bar') == 'bar'
    assert pm2.invoke_one('plugin_without_prob', 'bar') is None

    print(pm2.invoke_all('foo'))
    print(pm2.invoke_all('bar'))

    print('Test passed.')


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
