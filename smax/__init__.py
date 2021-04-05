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
