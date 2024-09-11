import traceback


class Hookable:
    def __init__(self, func):
        self._func = func
        self._pre_hooks = []
        self._post_hooks = []
        self._replace_hook = None
        self._hooked_instance = None

    def __call__(self, *args, **kwargs):
        for pre_hook in self._pre_hooks:
            pre_hook(*args, **kwargs)

        if self._hooked_instance:
            result = self._func(self._hooked_instance, *args, **kwargs) \
                if not self._replace_hook else self._replace_hook(self._hooked_instance, *args, **kwargs)
        else:
            result = self._func(*args, **kwargs) if not self._replace_hook else self._replace_hook(*args, **kwargs)

        for post_hook in self._post_hooks:
            post_hook(*args, **kwargs)

        return result

    def __get__(self, instance, owner):
        self._hooked_instance = instance
        return self

    def __repr__(self):
        return f"<Hooked Function {self._func.__name__}>"

    def add_pre_hook(self, hook):
        self._pre_hooks.append(hook)

    def remove_pre_hook(self, hook):
        self._pre_hooks.remove(hook)

    def add_post_hook(self, hook):
        self._post_hooks.append(hook)

    def remove_post_hook(self, hook):
        self._post_hooks.remove(hook)

    def set_replacement_hook(self, hook, force=False) -> bool:
        if self._replace_hook and not force:
            return False
        self._replace_hook = hook
        return True


# ----------------------------------------------------------------------------------------------------------------------


class Object1:
    def __init__(self):
        self.sum = 0

    @Hookable
    def obj_add(self, val):
        print(f'obj_add before: {self.sum}')
        self.sum += val
        print(f'obj_add after: {self.sum}')


g_sum = 0


@Hookable
def global_add(val):
    global g_sum
    print(f'global_add before: {g_sum}')
    g_sum += val
    print(f'global_add after: {g_sum}')


def _pre_hook(val):
    print(f'pre_hook: {val}')


def _after_hook(val):
    print(f'after_hook: {val}')


def main():
    obj = Object1()
    obj.obj_add(1)
    global_add(10)

    obj.obj_add.add_pre_hook(_pre_hook)
    obj.obj_add.add_post_hook(_after_hook)

    global_add.add_pre_hook(_pre_hook)
    global_add.add_post_hook(_after_hook)

    obj.obj_add(3)
    global_add(30)


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
