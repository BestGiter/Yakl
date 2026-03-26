class Function:
   def __init__(self, params, code, env):
       self.params = params
       self.code = code
       self.env = env
   def __repr__(self):
       args = ", ".join(self.params)
       return f"Function({args})"


class Object:
   def __init__(self, scope):
       self.env = scope
   def __repr__(self):
       return repr(self.env)




class BaseValue:
   def __init__(self, value):
       self.value = value
   def __repr__(self):
       return f"{str(self.value)}"


class List(BaseValue):
   pass


class Number(BaseValue):
   pass


class String(BaseValue):
   pass


class Nothing(BaseValue):
   def __init__(self):
       pass


class Value:
   def __init__(self, kind, value):
       self.type = kind
       self.value = value
   def __repr__(self):
       return f"{repr(self.value)}"




class Boolean(BaseValue):
   pass

def make_object(context, name, init, methods):
    obj_env = dict(init)
    obj = Value(name, Object(obj_env))
    for k, v in methods.items():
        obj_env[k] = Value("python-function", Object({"pyfunc": v, "env": context.env.copy()+[obj_env|{"this": obj}]}))
    return obj

def make_number(context, x):
    return make_object(context, "number", {"value": x}, {"__repr": lambda env: str(env[-1]["this"].value.env["value"]),
                                                         "__add": lambda env, other: make_number(context, env[-1]["this"].value.env["value"]+other.value.env["value"]),
                                                         "__sub": lambda env, other: make_number(context, env[-1]["this"].value.env["value"]-other.value.env["value"]),
                                                         "__mul": lambda env, other: make_number(context, env[-1]["this"].value.env["value"]*other.value.env["value"]),
                                                         "__div": lambda env, other: make_number(context, env[-1]["this"].value.env["value"]/other.value.env["value"]),
                                                         "__equ": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]==other.value.env["value"]),
                                                         "__neq": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]!=other.value.env["value"]),
                                                         "__gre": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]>other.value.env["value"]),
                                                         "__les": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]<other.value.env["value"]),
                                                         })

def make_string(context, x):
    return make_object(context, "string", {"value": x}, {"__repr": lambda env: str(env[-1]["this"].value.env["value"]),
                                                         "__add": lambda env, other: make_string(context, env[-1]["this"].value.env["value"]+other.value.env["value"]),
                                                         "__equ": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]==other.value.env["value"]),
                                                         "__neq": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]!=other.value.env["value"]),
                                                         })
def make_boolean(context, x):
    return make_object(context, "boolean", {"value": x}, {"__repr": lambda env: str(env[-1]["this"].value.env["value"]),
                                                          "__add": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"] or other.value.env["value"]),
                                                          "__mul": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"] and other.value.env["value"]),
                                                          "__equ": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]==other.value.env["value"]),
                                                          "__neq": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]!=other.value.env["value"]),
                                                          })
