import os
import traceback
from functools import partial
from inspect import getmembers, isfunction

from typing import List, Union

"""
A plug-in module should include following functions:
    plugin_prob() -> dict : Includes 'name', 'version', 'tags'
    plugin_capacities() -> [str] : Lists the capacity that module supports
"""


PLUGIN_PROB_FUNCTIONS = ['plugin_prob', 'plugin_capacities']


class PluginManager:
    class PluginData:
        def __init__(self, plugin_name: str, module_path: str, module_name: str, module_inst):
            self.plugin_name = plugin_name
            self.module_path = module_path
            self.module_name = module_name
            self.module_inst = module_inst

    def __init__(self, plugin_path: Union[str, List[str]] = '', prob_functions: [str] or None = None):
        self.__path = []
        self.__plugins = []
        self.__last_exception = None
        self.__last_traceback = None
        self.__prob_functions = PLUGIN_PROB_FUNCTIONS if prob_functions is None else prob_functions
        self.add_plugin(plugin_path)

    def add_plugin(self, plugin_path: str or [str]):
        if isinstance(plugin_path, str):
            if plugin_path.strip() != '':
                self.__path.append(plugin_path.strip())
        elif isinstance(plugin_path, (list, tuple, set)):
            self.__path.extend(list(plugin_path))

    def reload_plugin(self):
        all_plugin_data_list = []
        for plugin_path in self.__path:
            try:
                # Ensure all plugin path has been added to system path avoiding module can't find issue.

                if os.path.isdir(plugin_path):
                    if plugin_path not in os.sys.path:
                        os.sys.path.append(plugin_path)
                    plugin_data_list = self.__load_from_single_path(plugin_path)
                else:
                    import_path = os.path.dirname(plugin_path)
                    if import_path not in os.sys.path:
                        os.sys.path.append(import_path)
                    plugin_data_list = [self.__load_from_single_file(plugin_path)]

                all_plugin_data_list.extend(plugin_data_list)
            except Exception as e:
                self.__last_exception = e
                self.__last_traceback = traceback.format_exc()
                print('Load plugin from path % Fail.', plugin_path)
                print(e)
                print('Ignore...')
            finally:
                pass
        for plugin in all_plugin_data_list:
            self.__check_update_plugin_data(plugin)

    def get_plugin_data(self) -> [PluginData]:
        return self.__plugins.copy()

    def get_prob_functions(self) -> [str]:
        return self.__prob_functions

    def find_module_has_capacity(self, capacity: str) -> [object]:
        """
        Finds the module that supports the specified feature.
        :param capacity: The capacity you want to check.
        :return: The module list that has this capacity.
        """
        module_list = []
        for file_name, plugin in self.__plugins:
            if self.__safe_execute(plugin, 'plugin_adapt', capacity):
                module_list.append(plugin)
        return module_list

    def check_module_has_function(self, module: object, function: str) -> bool:
        try:
            return callable(getattr(module, function))
        except Exception as e:
            self.__last_exception = e
            self.__last_traceback = traceback.format_exc()
            print('Check callable: ' + str(e))
            return False
        finally:
            pass

    def get_module_functions(self, module: object) -> [str]:
        """
        Get function of a module.
        :param module: The module that you want to check. Not support list.
        :return: The function list of this module
        """
        # getmembers returns a list of (object_name, object_type) tuples.
        functions_list = [o for o in getmembers(module) if isfunction(o[1])]
        return functions_list

    def get_module_function_entry(self, module: object, _function: str):
        try:
            return getattr(module, _function)
        except Exception as e:
            print(e)
            return None
        finally:
            pass

    def execute_module_function(
            self, module: object or [object], _function: str, *args, **kwargs) -> object or [object]:
        """
        Execute function of Module
        :param module: The module that you want to execute its function.
        :param _function: The function you want to invoke
        :return: The object that the invoking function returns, it will be a list if the modules param is a list.
                 Includes None return.
        """
        self.clear_error()
        return self.__safe_execute(module, _function, *args, **kwargs)

    def execute_all_module_function(self, _function: str, *args, **kwargs) -> [object]:
        self.clear_error()
        for _, plugin in self.__plugins:
            self.__safe_execute(plugin, _function, *args, **kwargs)

    def clear_error(self):
        self.__last_exception = None
        self.__last_traceback = None

    def get_last_error(self) -> (Exception, str):
        return self.__last_exception, self.__last_traceback

    # ------------------------------- Search and Management -------------------------------

    def __load_from_single_path(self, plugin_path) -> list:
        """
        Refresh plugin list immediately. You should call this function if any updates to the plug-in folder.
        :return: None
        """

        plugin_list = []
        module_files = os.listdir(plugin_path)

        for file_name in module_files:
            if not file_name.endswith('.py') or file_name.startswith('_') or file_name.startswith('.'):
                continue
            module_data = self.__load_from_single_file(file_name)
            if module_data is not None:
                plugin_list.append(module_data)
        return plugin_list

    def __load_from_single_file(self, file_name: str) -> PluginData or None:
        plugin_name = os.path.splitext(file_name)[0]
        try:
            module = __import__(plugin_name)
            if module is None or not self.__check_prob_functions(module):
                raise ValueError('No prob functions.')
            return PluginManager.PluginData(plugin_name, file_name, plugin_name, module)
        except Exception as e:
            self.__last_exception = e
            self.__last_traceback = traceback.format_exc()
            print('When import module: ' + plugin_name)
            print(e)
            print(traceback.format_exc())
            print('Ignore...')
            return None
        finally:
            pass

    def __check_prob_functions(self, module) -> bool:
        for pf in self.__prob_functions:
            if not self.check_module_has_function(module, pf):
                return False
        return True

    def __check_update_plugin_data(self, plugin_data: PluginData):
        plugin_index = self.__find_plugin(plugin_data.module_name)
        if plugin_index >= 0:
            self.__plugins[plugin_index].module_name = plugin_data.module_name
            self.__plugins[plugin_index].module_path = plugin_data.module_path
            self.__plugins[plugin_index].module_inst = plugin_data.module_inst
        else:
            self.__plugins.append(plugin_data)

    def __find_plugin(self, plugin_name: str) -> int:
        for i in range(0, len(self.__plugins)):
            if self.__plugins[i].plugin_name == plugin_name:
                return i
        return -1

    # --------------------------------------- Execute ---------------------------------------

    def __safe_execute(self, module: object, _function: str, *argc, **argv) -> object:
        try:
            func = getattr(module, _function)
            return_obj = func(*argc, **argv)
        except Exception as e:
            self.__last_exception = e
            self.__last_traceback = traceback.format_exc()
            return_obj = None
            print("Function run fail.")
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
        finally:
            pass
        return return_obj


# ------------------------------------ Plug-in Wrapper ------------------------------------

"""
Plug-in wrapper
    20200214
    Easy invoke plug-in function.
"""


class PluginWrapper:
    """
    This wrapper and invoke plugin function directly.
    """
    def __init__(self, plugin: PluginManager, extension: any):
        self.__data = dict()
        self.__plugin = plugin
        self.__extension = extension

    def __getattr__(self, attr):
        return partial(self.invoke, attr)

    def set_data(self, k: str, v: any):
        self.__data[k] = v

    def get_data(self, k: str) -> any:
        return self.__data.get(k, None)

    def invoke(self, func: str, *args, **kwargs) -> any:
        try:
            result = self.plugin_manager().execute_module_function(self.__extension, func, kwargs)
            return result[0] if result is not None and len(result) > 0 else None
        except Exception as e:
            print('Invoke error: ' + str(e))
            print(traceback.format_exc())
            return None
        finally:
            pass

    def extension(self) -> any:
        return self.__extension

    def plugin_manager(self) -> PluginManager:
        return self.__plugin

    def clear_error(self):
        self.plugin_manager().clear_error()

    def get_last_error(self) -> (Exception, str):
        self.plugin_manager().get_last_error()


