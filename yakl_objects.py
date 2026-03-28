class Object:
  def __init__(self, scope):
      self.env = scope
  def __repr__(self):
      return repr(self.env)






class Value:
  def __init__(self, kind, value):
      self.type = kind
      self.value = value
  def __repr__(self):
      return f"{repr(self.value)}"


def make_object(context, name, init, methods):
   obj_env = init
   obj = Value(name, Object(obj_env))
   obj_env["this"] = obj
   for k, v in methods.items():
       obj_env[k] = Value("python-function", Object({"pyfunc": v, "env": context.env+[obj_env]}))
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
   return make_object(context, "string", {"length": len(x)}|{i: make_character(context, xs) for i, xs in enumerate(x)}, {"__repr": lambda env: get_value(env[-1]["this"]),
                                                        "__add": lambda env, other: make_string(context, str(get_value(env[-1]["this"])+str(get_value(other)))),
                                                        "__equ": lambda env, other: make_boolean(context, get_value(env[-1]["this"])==get_value(other)),
                                                        "__neq": lambda env, other: make_boolean(context, get_value(env[-1]["this"])!=get_value(other)),
                                                        })
def make_character(context, x):
   return make_object(context, "character", {"value": x}, {"__repr": lambda env: str(env[-1]["this"].value.env["value"]),
                                                           "__add": lambda env, other: make_string(context, "".join(get_value(env[-1]["this"])+get_value(other))),
   })
def make_boolean(context, x):
   return make_object(context, "boolean", {"value": x}, {"__repr": lambda env: str(env[-1]["this"].value.env["value"]),
                                                         "__add": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"] or other.value.env["value"]),
                                                         "__mul": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"] and other.value.env["value"]),
                                                         "__equ": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]==other.value.env["value"]),
                                                         "__neq": lambda env, other: make_boolean(context, env[-1]["this"].value.env["value"]!=other.value.env["value"]),
                                                         })
def make_function(context, params, code):
   return make_object(context, "function", {"params": params, "code": code, "env": context.env+[{}]}, {"__call": lambda env, *x: context.pycall(env[-1]["this"], x)})


def get_string_value(string):
   return str("".join([v.value.env["value"] for k, v in string.value.env.items() if isinstance(k, int)]))


def get_list_value(string):
   return [v.value.env["value"] for k, v in string.value.env.items() if isinstance(k, int)]




def get_value(val):
   if val.type == "string":
       return get_string_value(val)
   elif val.type == "number":
       return val.value.env["value"]
   elif val.type == "character":
       return val.value.env["value"]
   elif val.type == "list":
       return get_list_value(val)






