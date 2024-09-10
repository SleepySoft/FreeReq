import traceback


class MonkeyHook:
    def __init__(self, original_func, hook_before=None, hook_replace=None, hook_after=None):
        self.original_func = original_func
        self.original_func_code = original_func.__code__
        self.original_func_name = original_func.__name__

        self.try_hook_global_func(original_func) or self.try_hook_object_func(original_func)

        # original_func.__code__ = MonkeyHook.foo.__code__
        #
        # if isinstance(hook_before, (list, tuple, set)):
        #     self.hook_func_before = list(hook_before)
        # elif hook_before:
        #     self.hook_func_before = [hook_before]
        # else:
        #     self.hook_func_before = []
        #
        # self.hook_func_replace = hook_replace
        #
        # if isinstance(hook_after, (list, tuple, set)):
        #     self.hook_func_after = list(hook_after)
        # elif hook_after:
        #     self.hook_func_after = [hook_after]
        # else:
        #     self.hook_func_after = []

    def try_hook_global_func(self, original_func):
        try:
            original_func.__code__ = self.__hook_global_func.__func__.__code__
            return True
        except Exception as e:
            print(str(e))
            return False
        finally:
            pass

    def try_hook_object_func(self, original_func):
        try:
            original_func.__func__.__code__ = self.__hook_object_func.__func__.__code__
            return True
        except Exception as e:
            print(str(e))
            return False
        finally:
            pass

    def __hook_global_func(self, *args, **kwargs):
        print(self)
        print(args)
        print(kwargs)

    def __hook_object_func(self, self_or_cls, *args, **kwargs):
        print(self)
        print(self_or_cls)
        print(args)
        print(kwargs)

    def hook_function(self, func, *args, **kwargs):
        if func != self.original_func_name:
            return
        for hook_func in self.hook_func_before:
            hook_func(*args, **kwargs)
        ret = self.hook_func_replace(*args, **kwargs) \
            if self.hook_func_replace is not None else self.original_func(*args, **kwargs)
        for hook_func in self.hook_func_before:
            hook_func(*args, **kwargs)
        return ret

    def restore(self):
        return self.original_func


# ---------------------------------------------------------------------------------------------------------------------

class Object:
    def __init__(self):
        pass

    def obj_func(self, a, b):
        print('--------------- obj_func ---------------')
        print(self)
        print(a)
        print(b)
        print('----------------------------------------')


def global_func(x, y):
    print('------------- global_func --------------')
    print(x)
    print(y)
    print('----------------------------------------')


def global_hook_obj_func_before(a, b):
    print('---------- global_hook_obj_func_before ----------')
    print(a)
    print(b)
    print('-------------------------------------------------')


def global_hook_obj_func_after(a, b):
    print('---------- global_hook_obj_func_after ----------')
    print(a)
    print(b)
    print('------------------------------------------------')


def main():
    obj = Object()
    obj.obj_func(1, True)
    global_func('foo', ['bar'])

    MonkeyHook(obj.obj_func, hook_before=global_hook_obj_func_before, hook_after=global_hook_obj_func_after)

    obj.obj_func(1, True)


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





