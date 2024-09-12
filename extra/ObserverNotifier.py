import traceback


class ObserverNotifier:
    """
    A class to simplify the observer notification.
    You call notify_xxx on this class and all observer's on_xxx function will be invoked.
    """
    def __init__(self):
        self.__observers = []

    def add_observer(self, observer):
        if observer not in self.__observers:
            self.__observers.append(observer)

    def remove_observer(self, observer):
        if observer in self.__observers:
            self.__observers.remove(observer)

    def __getattr__(self, item):
        if item.startswith('notify_'):
            action = item[len('notify_'):]

            def dynamic_notify(*args, **kwargs):
                method_name = f"on_{action}"
                for observer in self.__observers:
                    try:
                        getattr(observer, method_name)(*args, **kwargs)
                    except AttributeError:
                        print(f"Warning: Observer {observer} does not implement method {method_name}")
                    except Exception as e:
                        print(str(e))
                print(f"=> {action.capitalize()} notified.")

            return dynamic_notify
        else:
            return None


class IExampleObserver:
    def on_req_saved(self, req_uri):
        print(f"Observer: Req saved {req_uri}")


def main():
    # 创建类的实例
    notifier = ObserverNotifier()

    # 创建观察者实例
    observer = IExampleObserver()

    # 添加观察者
    notifier.add_observer(observer)

    # 动态调用通知方法
    notifier.notify_req_saved("http://example.com")  # 正常调用观察者的 on_req_saved 方法
    notifier.notify_req_loaded("http://example.com")  # 如果没有实现 on_req_loaded，将打印警告


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
