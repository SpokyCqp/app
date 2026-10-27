"""
PyVault - Python Code Obfuscation Tool
Supports Python versions: 3.11, 3.12, 3.13, 3.14
"""

import io, os, sys, time, threading, ctypes, inspect, traceback, marshal, base64, zlib
from queue import Queue
import tempfile
import zipfile
import shutil
import platform
import shlex
import binascii
from base64 import b85encode
from concurrent.futures import ThreadPoolExecutor
import random

MAX_ARGS = 128
TCC_OUTPUT_EXE = 2

class TCCState(ctypes.Structure):
    pass

TCCStatePtr = ctypes.POINTER(TCCState)

def get_lib_for_target(target):
    base = "/data/data/com.pyvault/files/toolchain/"
    return {
        "x86_64-linux-gnu": base + "libtcc-linux.so",
        "x86_64-windows-gnu": base + "libtcc-win64.so",
        "aarch64-linux-android": base + "libtcc-arm64.so",
        "arm-linux-androideabi": base + "libtcc-arm.so"
    }.get(target)

def split_args(argstr):
    return shlex.split(argstr)

def tcc_compile(argstr):
    argv = split_args(argstr)
    argc = len(argv)
    target = None
    input_file = None
    output_file = None
    include_dirs = []
    lib_dirs = []
    libs = []
    options = []
    i = 0

    while i < argc:
        arg = argv[i]
        if arg.startswith("-I"):
            include_dirs.append(arg[2:])
        elif arg.startswith("-L"):
            lib_dirs.append(arg[2:])
        elif arg.startswith("-l"):
            libs.append(arg[2:])
        elif arg == "-o" and i + 1 < argc:
            output_file = argv[i + 1]
            i += 1
        elif arg == "--target" and i + 1 < argc:
            target = argv[i + 1]
            i += 1
        elif arg.endswith(".c"):
            input_file = arg
        else:
            options.append(arg)
        i += 1

    if not target or not input_file or not output_file:
        print("Usage: '-Wall -O2 -Iinc -Llib -lm -o out input.c --target triplet'")
        return -1

    libname = get_lib_for_target(target)
    if not libname or not os.path.exists(libname):
        print(f"Unknown or missing target library: {target}")
        return -2

    try:
        lib = ctypes.CDLL(libname)
    except Exception as e:
        print(f"Failed to load library: {libname}\nError: {e}")
        return -3

    try:
        tcc_new = lib.tcc_new
        tcc_new.restype = TCCStatePtr
        tcc_delete = lib.tcc_delete
        tcc_delete.argtypes = [TCCStatePtr]
        tcc_set_output_type = lib.tcc_set_output_type
        tcc_set_output_type.argtypes = [TCCStatePtr, ctypes.c_int]
        tcc_add_include_path = lib.tcc_add_include_path
        tcc_add_include_path.argtypes = [TCCStatePtr, ctypes.c_char_p]
        tcc_add_library_path = lib.tcc_add_library_path
        tcc_add_library_path.argtypes = [TCCStatePtr, ctypes.c_char_p]
        tcc_add_library = lib.tcc_add_library
        tcc_add_library.argtypes = [TCCStatePtr, ctypes.c_char_p]
        tcc_add_file = lib.tcc_add_file
        tcc_add_file.argtypes = [TCCStatePtr, ctypes.c_char_p]
        tcc_output_file = lib.tcc_output_file
        tcc_output_file.argtypes = [TCCStatePtr, ctypes.c_char_p]
        try:
            tcc_add_option = lib.tcc_add_option
            tcc_add_option.argtypes = [TCCStatePtr, ctypes.c_char_p]
        except AttributeError:
            tcc_add_option = None
    except AttributeError as e:
        print(f"Missing required symbols in {libname}:\n{e}")
        return -4

    s = tcc_new()
    if not s:
        print("Failed to create state")
        return -5

    tcc_set_output_type(s, TCC_OUTPUT_EXE)
    for path in include_dirs:
        tcc_add_include_path(s, path.encode())
    for path in lib_dirs:
        tcc_add_library_path(s, path.encode())
    for libname in libs:
        tcc_add_library(s, libname.encode())
    if tcc_add_option:
        for opt in options:
            tcc_add_option(s, opt.encode())
    if tcc_add_file(s, input_file.encode()) < 0:
        print("Failed to add source file")
        tcc_delete(s)
        return -6
    if tcc_output_file(s, output_file.encode()) < 0:
        print("Failed to output file")
        tcc_delete(s)
        return -7
    tcc_delete(s)
    return 0

class PyVaultObfuscation:
    """Main obfuscation class supporting Python 3.11-3.14"""
    GCC_FLAGS = " -s "
    ARM64_TARGET = "aarch64-linux-android"
    ARMV7_TARGET = "arm-linux-androideabi"
    WINDOWS_TARGET = "x86_64-windows-gnu"
    LINUX_TARGET = "x86_64-linux-gnu"

    SUPPORTED_PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]

    def __init__(self, python_version="3.12", log_function=None):
        self.log = log_function or print
        self.python_version = python_version
        self.armv7file_path = None
        self.arm64file_path = None
        self.win_file_path = None
        self.linux_file_path = None

    def log_message(self, level, message):
        print(f"[{level}] {message}")

    def replace_def_in_file(self, file_path):
        self.log_message("LOG", f"Adjusting C code for Python {self.python_version} compatibility.")
        problematic_code = (
            "#ifdef SIZEOF_VOID_P\n"
            "    enum { __pyx_check_sizeof_voidp = 1 / (int)(SIZEOF_VOID_P == sizeof(void*)) };\n"
            "  #endif"
        )
        fixed_code = (
            "#ifdef SIZEOF_VOID_P\n"
            "  #if (SIZEOF_VOID_P == 8)\n"
            "    enum { __pyx_check_sizeof_voidp = 1 / (int)(SIZEOF_VOID_P == sizeof(void*)) };\n"
            "  #else\n"
            "    enum { __pyx_check_sizeof_voidp = (int)0 };\n"
            "  #endif\n"
            "#endif"
        )
        try:
            with open(file_path, "r") as file:
                content = file.read()
            if problematic_code in content:
                updated_content = content.replace(problematic_code, fixed_code)
                with open(file_path, "w") as file:
                    file.write(updated_content)
                self.log_message("SUCCESS", f"Code adjusted for Python {self.python_version}.")
            else:
                self.log_message("LOG", f"Skipping - no adjustment needed.")
        except FileNotFoundError:
            self.log_message("ERROR", f"File not found: {file_path}")
        except Exception as e:
            self.log_message("ERROR", f"Error: {e}")

    def compile_c_to_executable(self, c_file, output_file, target_triplet):
        include_paths = {
            "x86_64-windows-gnu": f"/data/data/com.pyvault/files/toolchain/x86_64-win32/include/python{self.python_version}",
            "x86_64-linux-gnu": f"/data/data/com.pyvault/files/toolchain/x86_64-linux-gnu/include/python{self.python_version}",
            "aarch64-linux-android": f"/data/data/com.pyvault/files/toolchain/sysroot/include/aarch64-linux-android/python{self.python_version}",
            "arm-linux-androideabi": f"/data/data/com.pyvault/files/toolchain/sysroot/include/arm-linux-androideabi/python{self.python_version}",
        }
        lib_names = {
            "x86_64-windows-gnu": f"python{self.python_version.replace('.', '')}",
            "x86_64-linux-gnu": f"python{self.python_version.replace('.', '')}",
            "aarch64-linux-android": f"python{self.python_version.replace('.', '')}",
            "arm-linux-androideabi": f"python{self.python_version.replace('.', '')}",
        }

        include_path = include_paths.get(target_triplet)
        lib_name = lib_names.get(target_triplet)

        if not include_path or not lib_name:
            self.log_message("ERROR", f"Unsupported target: {target_triplet}")
            return 1

        args = (
            f'-o "{output_file}" '
            f'-I"{include_path}" '
            f'--target {target_triplet} {self.GCC_FLAGS} "{c_file}" '
            f'-l{lib_name}'
        )

        result = tcc_compile(args)
        if result != 0:
            self.log_message("ERROR", f"Compile failed with code {result}")
        return result

    @staticmethod
    def read_binary_file(filename):
        try:
            with open(filename, "rb") as file:
                return file.read()
        except:
            return None

    def create_zip_in_memory(self):
        try:
            zip_buffer = tempfile.SpooledTemporaryFile()
            with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                zipf.writestr("__main__.py", self.main_script())
                zipf.writestr("arm64-v8a", self.read_binary_file(self.arm64file_path) or b'')
                zipf.writestr("armeabi-v7a", self.read_binary_file(self.armv7file_path) or b'')
                zipf.writestr("x86_64.exe", self.read_binary_file(self.win_file_path) or b'')
                zipf.writestr("x86_64-linux", self.read_binary_file(self.linux_file_path) or b'')
            zip_buffer.seek(0)
            data = zip_buffer.read()
            zip_buffer.close()
            return data
        except Exception as e:
            self.log_message("ERROR", f"Error creating zip: {e}")
            return None

    @staticmethod
    def main_script():
        return """import zipfile, os, shutil, tempfile, sys, platform

def main():
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    temp_dir = tempfile.mkdtemp()
    try:
        script_path = os.path.abspath(sys.argv[0])
        with zipfile.ZipFile(script_path, 'r') as zip_file:
            zip_file.extractall(temp_dir)
        machine_arch = platform.machine()
        arch_mapping = {
            'armv7l': 'armeabi-v7a',
            'aarch64': 'arm64-v8a',
            'x86_64': 'x86_64-linux',
            'amd64': 'x86_64-linux',
            'AMD64': 'x86_64.exe',
        }
        if machine_arch not in arch_mapping:
            print(f'Unsupported: {machine_arch}')
            sys.exit(1)
        target_file = os.path.join(temp_dir, arch_mapping[machine_arch])
        if not os.path.exists(target_file):
            print(f'Missing: {target_file}')
            sys.exit(1)
        os.chmod(target_file, 0o755)
        prefix = sys.prefix
        env_vars = os.environ
        if 'com.termux' in prefix or 'TERMUX_VERSION' in env_vars or prefix.startswith('/data/data/com.termux'):
            os.system(f'LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib {target_file}')
        else:
            os.system(target_file)
    except Exception as e:
        print(f'Error: {e}')
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    main()
"""

    @staticmethod
    def python_code(zip_data):
        return f"""
import os
from base64 import b85decode
file_name = '.encrypted'
source = b85decode({zip_data})
try:
    with open(file_name, 'wb') as file:
        file.write(source)
    os.system('python .encrypted')
except Exception as e:
    print(e)
finally:
    if os.path.exists(file_name):
        os.remove(file_name)
"""

    def process_code(self, python_code):
        try:
            temp_dir = tempfile.mkdtemp()
            py_file_path = os.path.join(temp_dir, "temp_script.py")
            self.armv7file_path = os.path.join(temp_dir, "armeabi-v7a")
            self.arm64file_path = os.path.join(temp_dir, "arm64-v8a")
            self.win_file_path = os.path.join(temp_dir, "x86_64.exe")
            self.linux_file_path = os.path.join(temp_dir, "x86_64-linux")

            with open(py_file_path, "w") as py_file:
                py_file.write(python_code)

            self.log_message("INFO", f"Python {self.python_version} - Compilation not available on this platform")

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.log_message("ERROR", f"Cleanup error: {e}")

            return self.bytecode_obfuscate(python_code)

        except Exception as e:
            self.log_message("ERROR", f"Error: {e}")
            raise

    def bytecode_obfuscate(self, source_code: str) -> str:
        """Obfuscate using marshal + zlib + base85"""
        code_obj = compile(source_code, '<string>', 'exec')
        marshalled_code = marshal.dumps(code_obj)
        compressed_code = zlib.compress(marshalled_code)
        encoded_code = base64.b85encode(compressed_code).decode('utf-8')
        obfuscated_script = f"""import marshal, zlib, base64
exec(marshal.loads(zlib.decompress(base64.b85decode("{encoded_code}"))))
"""
        return obfuscated_script

    def obfuscate_code_minify(self, source_code: str) -> str:
        """Simple minification - remove comments and extra whitespace"""
        import re
        # Remove comments
        code = re.sub(r'#.*$', '', source_code, flags=re.MULTILINE)
        # Remove extra whitespace
        code = re.sub(r'\n\s*\n', '\n', code)
        code = re.sub(r'  +', ' ', code)
        return code.strip()

def _async_raise(tid, exctype):
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    tid = ctypes.c_long(tid)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("Invalid thread ID")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("SetAsyncExc failed")

def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

def run_with_timeout(target, args=(), timeout=15):
    result_queue = Queue()
    def wrapper():
        try:
            result = target(*args)
            result_queue.put((True, result))
        except Exception as e:
            result_queue.put((False, e))
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        stop_thread(thread)
        raise TimeoutError("Operation timed out")
    success, result = result_queue.get()
    if success:
        return result
    else:
        raise result

def obfuscate_thread_run(code, python_version="3.12"):
    try:
        ob = PyVaultObfuscation(python_version=python_version)
        return ob.bytecode_obfuscate(code)
    except Exception as e:
        print("Obfuscation error:", e)
        return None

def main_obfuscate(source_code, python_version="3.12"):
    return run_with_timeout(obfuscate_thread_run, args=(source_code, python_version))

def get_supported_versions():
    return PyVaultObfuscation.SUPPORTED_PYTHON_VERSIONS