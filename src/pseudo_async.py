from threading import Thread
# copied from Linux Mint's code
# a decorator that makes a function run in background via threading
def _async(func):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper