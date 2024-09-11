class ObserverNotifier:
    def __init__(self):
        self.observer = []

    def notify(self, method_name, *args, **kwargs):
        print(f"=>{method_name}.")
        for ob in self.observer:
            func_name = f"on_{method_name}"
            func_inst = getattr(ob, func_name)
            try:
                if func_inst:
                    func_inst(*args, **kwargs)
                else:
                    print(f'Warning: Observer {ob} has no method {func_name}')
            except Exception as e:
                print(str(e))
            finally:
                pass
