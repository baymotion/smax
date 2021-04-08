#

import types

from .parser import load_source
from .reactor import Reactor
from .select_reactor import SelectReactor
from .translate import parse, generate_python, generate_yaml, translate

def compile_python(python_code, module_name="state_machine"):
    """
        Returns a module with the given name.
    """
    # Create the module we're return with
    m = types.ModuleType(module_name)
    exec(python_code, m.__dict__)
    # Normally you'd add the module to sys.modules
    # but we only want this module to be visible
    # to the caller.
    return m

def load(filename, class_name, save_generated_python=None):
    """ We cache the compiled results from filename
        so you can get other machine class implementations
        from this same file quickly.
    """
    global smax_modules
    module = smax_modules.get(filename, None)
    if module is None:
        spec = load_source(filename)
        python_code = translate(spec, filename)
        if save_generated_python:
            with open(save_generated_python, "wt") as f:
                f.write(python_code)
        module = compile_python(python_code)
        smax_modules[filename] = module
    return module.__dict__[class_name]

smax_modules = { }

