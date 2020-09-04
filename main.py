import os
import sys
from sandbox import sandbox_inout
import io
import uuid
import time
import threading
import ctypes
import inspect

ROOT = os.path.abspath(os.path.dirname(__file__))
venv_folder = os.path.join(ROOT, ".venv")
print(venv_folder)
if not os.path.exists(venv_folder):
    import venv
    print("Creating virtal environment")
    venv.create(venv_folder,clear=True, with_pip=True)
    print("Make sure to launch the virtual environment after installing the requirements")
    print("pip3 install -r requirements.txt")
    sys.exit(1)

from RestrictedPython import compile_restricted
from AccessControl.ZopeGuards import safe_builtins
from AccessControl.ZopeGuards import get_safe_globals
from RestrictedPython.Guards import full_write_guard

def run_code(file_path, scoped_globals, scoped_locals):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    file_handle = open(file_path, "r")
    source_code  = "".join(file_handle.readlines())
    file_handle.close()
    print("Riunning code")

    byte_code = compile_restricted(
        source_code,
        filename=file_path,
        mode='exec'
    )
    try:
        exec(byte_code, scoped_globals, scoped_locals)
    except TimeoutError:
        pass

class Bot(object):
    def __init__(self, bot_id, code_path):
        self.bot_id = bot_id
        self.sin = sandbox_inout.SandboxInOut()
        self.sout = sandbox_inout.SandboxInOut()
        self.code_location = code_path
        self.__alive = False
        self.task = None
        self.start_time = None

    def execute(self):
        self.__alive = True
        restricted_globals = get_safe_globals()
        restricted_globals["input"] = self.sin.reader()
        restricted_globals["_print_"] = self.sout.printer()
        restricted_globals["sleep"] = time.sleep
        restricted_globals["log"] = lambda x: print(f"{self.bot_id}: {x}")
        local_vars = {}
        self.task = threading.Thread(group=None, target=run_code, args=(self.code_location, restricted_globals, local_vars), name=self.bot_id)
        self.start_time = time.time()
        self.task.start()
        return self.task

    def read(self):
        self.sout.readline()
    
    def write(self, data):
        self.sin.write(data,consumer=False)
        self.sin.stream.seek(0,0)

    def wait(self):
        self.task.join()

    def _kill(self, exception_type):
        if not self.task.is_alive():
            return
        if not inspect.isclass(exception_type):
            raise TypeError("Only types can be raised (not instances)")
        tid = self.task.native_id
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),
                                                     ctypes.py_object(exception_type))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        self.task.join(timeout=1)

    def _check_timeout_passed(self):
        if time.time() - self.start_time > 40:
            print(f"{self.bot_id} has lived too long and died")
            self._kill(TimeoutError)

    def is_alive(self):
        if self.task is None:
            return False
        if not self.task.is_alive():
            return False
        try:
            self._check_timeout_passed()
        except TimeoutError:
            pass
        return True

bots = {}
def create_bot(code_location):
    bot_id = uuid.uuid4()
    bot = Bot(bot_id, code_location)
    bots[bot_id] = bot
    print(f"Created bot {bot_id}")
    return bot

def main():
    file_path = os.path.join(ROOT, "data", "test.py")
    bot1 = create_bot(file_path)
    bot2 = create_bot(file_path)
    bot1.execute()
    bot2.execute()

    try:
        while bot1.is_alive() or bot2.is_alive():
            # print("Waiting for bots to die")
            time.sleep(0.5)
            bot1.write("done\n")
            bot2.write("done\n")
        print("End of the line")
    except KeyboardInterrupt:
        print("Ending early")
        bot1._kill(TimeoutError)
        bot2._kill(TimeoutError)

if __name__ == "__main__":
    main()
