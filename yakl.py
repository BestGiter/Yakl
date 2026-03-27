from yakl_objects import *
import importlib.util
import sys








def import_python_file(path):
   name = path.replace("/", "_").replace("\\", "_")
   spec = importlib.util.spec_from_file_location(name, path)
   module = importlib.util.module_from_spec(spec)
   sys.modules[name] = module
   spec.loader.exec_module(module)
   return module








def get_file(place):
   content = ""
   with open(place, "r") as f:
       content = f.read()
   return content








code = get_file("main.yakl")








class Node:
   def __init__(self, k, v, e, c):
       self.kind = k
       self.value = v
       self.extra = e
       self.children = c




   def __repr__(self):
       return f"Node({repr(self.kind)}, {repr(self.value)}, {repr(self.extra)}, {repr(self.children)})"








class Result:
   def __init__(self, ok, backtrack, value, message=None, index=None):
       self.ok = ok
       self.backtrack = backtrack
       self.value = value
       self.message = message
       self.index = index




   def failed(self):
       return not self.ok




   def backtracked(self):
       return self.backtrack




   def errored(self):
       return not self.ok and not self.backtrack




   def __repr__(self):
       return f"Result({repr(self.ok)}, {repr(self.backtrack)}, {repr(self.value)}, {repr(self.message)}, {repr(self.index)})"








class Parser:
   def __init__(self, code):
       self.code = code
       self.i = 0




   def Ok(self, item):
       return Result(True, False, item)




   def Backtrack(self):
       return Result(False, True, None)




   def Error(self, msg):
       return Result(False, False, None, msg, self.i)




   def is_end(self):
       return self.i >= len(self.code)




   def get_character(self):
       return self.code[self.i] if not self.is_end() else "\0"




   def skip_whitespace(self):
       while not self.is_end() and self.get_character() in " \t\n\r":
           self.i += 1




   def advance(self):
       c = self.get_character()
       self.i += 1
       return c




   def match(self, c):
       i = 0
       save = self.i
       while self.advance() == c[i]:
           i += 1
           if i == len(c):
               return True
       self.i = save
       return False




   def parse_number(self):
       self.skip_whitespace()
       save = self.i




       num = ""




       # Optional sign
       c = self.get_character()
       if c in "+-":
           num += self.advance()




       digits_before = False
       digits_after = False




       # Digits before decimal
       while self.get_character().isdigit():
           digits_before = True
           num += self.advance()




       # Decimal point
       if self.get_character() == ".":
           num += self.advance()




           # Digits after decimal
           while self.get_character().isdigit():
               digits_after = True
               num += self.advance()




       # If no digits at all, not a number
       if not digits_before and not digits_after:
           self.i = save
           return self.Backtrack()




       # Determine type
       is_float = "." in num




       # Convert
       value = float(num) if is_float else int(num)




       return self.Ok(Node("NUMBER", value, {"float": is_float}, []))




   def parse_string(self):
       self.skip_whitespace()
       save = self.i




       if not self.match('"'):
           return self.Backtrack()




       s = ""




       while not self.is_end():
           c = self.advance()




           if c == '"':
               return self.Ok(Node("STRING", s, {}, []))




           if c == "\\":
               if self.is_end():
                   return self.Error("Unterminated escape")




               esc = self.advance()




               if esc == "n":
                   s += "\n"
               elif esc == "t":
                   s += "\t"
               elif esc == '"':
                   s += '"'
               elif esc == "\\":
                   s += "\\"
               else:
                   return self.Error("Unknown escape: \\" + esc)
           else:
               s += c




       self.i = save
       return self.Error("Unterminated string")




   def parse_identifier(self):
       self.skip_whitespace()
       save = self.i




       c = self.get_character()
       if not (c.isalpha() or c == "_"):
           return self.Backtrack()




       ident = ""
       ident += self.advance()




       while True:
           c = self.get_character()
           if c.isalnum() or c == "_":
               ident += self.advance()
           else:
               break




       if ident in ["bound", "function", "if", "while", "object"]:
           self.i = save
           return self.Backtrack()




       return self.Ok(Node("IDENT", ident, {}, []))




   def parse_params(self):
       # SIMILAR RULE, REPLACE FEW STUFF
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_identifier()
       if multiplicative.failed():
           if multiplicative.errored():
               return multiplicative
           return self.Ok(Node("ITEMS", None, {}, []))
       base = multiplicative
       next_ = self.Ok(None)
       children = [base.value]
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match(","):
               OP = "COMMA"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_identifier()
           if next_.failed():
               self.i = save
               break
           children.append(next_.value)
       if next_.errored():
           return next_
       return self.Ok(Node("ITEMS", None, {}, children))




   def parse_items(self):
       # SIMILAR RULE, REPLACE FEW STUFF
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_expression()
       if multiplicative.failed():
           if multiplicative.errored():
               return multiplicative
           return self.Ok(Node("ITEMS", None, {}, []))
       base = multiplicative
       next_ = self.Ok(None)
       children = [base.value]
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match(","):
               OP = "COMMA"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_expression()
           if next_.failed():
               self.i = save
               break
           children.append(next_.value)
       if next_.errored():
           return next_
       return self.Ok(Node("ITEMS", None, {}, children))




   def parse_object(self):
       self.skip_whitespace()
       save = self.i
       if self.match("object"):
           self.skip_whitespace()
           if self.match("{"):
               self.skip_whitespace()
               code = self.parse_block()
               if not code.failed():
                   self.skip_whitespace()
                   if self.match("}"):
                       return self.Ok(Node("OBJ", None, {}, [code.value]))
       self.i = save
       return self.Backtrack()




   def parse_function(self):
       self.skip_whitespace()
       save = self.i
       if self.match("function"):
           self.skip_whitespace()
           if self.match("("):
               self.skip_whitespace()
               parameters = self.parse_params()
               if not parameters.failed():
                   self.skip_whitespace()
                   if self.match(")"):
                       self.skip_whitespace()
                       if self.match("{"):
                           self.skip_whitespace()
                           code = self.parse_block()
                           if not code.failed():
                               self.skip_whitespace()
                               if self.match("}"):
                                   return self.Ok(
                                       Node(
                                           "FUNC",
                                           None,
                                           {},
                                           [parameters.value, code.value],
                                       )
                                   )
       self.i = save
       return self.Backtrack()




   def parse_primary(self):
       while True:
           self.skip_whitespace()
           value = None
           string = self.parse_string()
           if not string.failed():
               value = string
               break
           ident = self.parse_identifier()
           if not ident.failed():
               value = ident
               break
           number = self.parse_number()
           if not number.failed():
               value = number
               break
           object_ = self.parse_object()
           if not object_.failed():
               value = object_
               break
           save = self.i
           if self.match("("):
               self.skip_whitespace()
               expr = self.parse_expression()
               self.skip_whitespace()
               if not expr.failed():
                   if self.match(")"):
                       value = expr
                       break
           self.i = save
           if self.match("["):
               self.skip_whitespace()
               items = self.parse_items()
               if not items.failed():
                   self.skip_whitespace()
                   if self.match("]"):
                       value = self.Ok(Node("LIST", None, {}, [items.value]))
                       break
           self.i = save
           function = self.parse_function()
           if not function.failed():
               value = function
               break
           self.i = save
           return self.Backtrack()
       while True:
           self.skip_whitespace()
           save = self.i
           if self.match("("):
               self.skip_whitespace()
               params = self.parse_items()
               if not params.failed():
                   self.skip_whitespace()
                   if self.match(")"):
                       value = self.Ok(
                           Node("CALL", None, {}, [value.value, params.value])
                       )
                       continue
               else:
                   print(params)
           self.i = save
           if self.match("["):
               self.skip_whitespace()
               expr = self.parse_expression()
               if not expr.failed():
                   self.skip_whitespace()
                   if self.match("]"):
                       value = self.Ok(
                           Node("INDEX", None, {}, [value.value, expr.value])
                       )
                       continue
           self.i = save
           if self.match("."):
               self.skip_whitespace()
               ident = self.parse_identifier()
               if not ident.failed():
                   value = self.Ok(
                       Node("INDEX", None, {}, [value.value, Node("STRING", ident.value.value, {}, [])])
                   )
                   continue
           self.i = save
           break
       return value




   def parse_multiplicative(self):
       # SIMILAR RULE, REPLACE FEW STUFF
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_primary()
       if multiplicative.failed():
           return multiplicative
       base = multiplicative
       next_ = self.Ok(None)
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match("*"):
               OP = "MUL"
           elif self.match("/"):
               OP = "DIV"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_primary()
           if next_.failed():
               self.i = save
               break
           base = self.Ok(Node(OP, None, {}, [base.value, next_.value]))
       if next_.errored():
           return next_
       return base




   def parse_additive(self):
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_multiplicative()
       if multiplicative.failed():
           return multiplicative
       base = multiplicative
       next_ = self.Ok(None)
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match("+"):
               OP = "ADD"
           elif self.match("-"):
               OP = "SUB"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_multiplicative()
           if next_.failed():
               self.i = save
               break
           base = self.Ok(Node(OP, None, {}, [base.value, next_.value]))
       if next_.errored():
           return next_
       return base




   def parse_relational(self):
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_additive()
       if multiplicative.failed():
           return multiplicative
       base = multiplicative
       next_ = self.Ok(None)
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match(">"):
               OP = "GRE"
           elif self.match("<"):
               OP = "LES"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_additive()
           if next_.failed():
               self.i = save
               break
           base = self.Ok(Node(OP, None, {}, [base.value, next_.value]))
       if next_.errored():
           return next_
       return base




   def parse_equality(self):
       #      additive := multiplicative (("+" | "-") multiplicative)*
       # ELSE backtrack
       multiplicative = self.parse_relational()
       if multiplicative.failed():
           return multiplicative
       base = multiplicative
       next_ = self.Ok(None)
       while True:
           save = self.i
           self.skip_whitespace()
           if self.match("=="):
               OP = "EQU"
           elif self.match("!="):
               OP = "NEQ"
           else:
               self.i = save
               break
           self.skip_whitespace()
           next_ = self.parse_relational()
           if next_.failed():
               self.i = save
               break
           base = self.Ok(Node(OP, None, {}, [base.value, next_.value]))
       if next_.errored():
           return next_
       return base




   def parse_control(self):
       # if := "if" expr "{" block "}" |OR| equality
       self.skip_whitespace()
       save = self.i
       if self.match("if"):
           self.skip_whitespace()
           condition = self.parse_expression()
           if not condition.failed():
               self.skip_whitespace()
               if self.match("{"):
                   self.skip_whitespace()
                   code = self.parse_block()
                   if not code.failed():
                       self.skip_whitespace()
                       if self.match("}"):
                           self.skip_whitespace()
                           save2 = self.i
                           if self.match("else"):
                               self.skip_whitespace()
                               if self.match("{"):
                                   self.skip_whitespace()
                                   code2 = self.parse_block()
                                   if not code2.failed():
                                       self.skip_whitespace()
                                       if self.match("}"):
                                           return self.Ok(
                                               Node(
                                                   "IF",
                                                   None,
                                                   {},
                                                   [
                                                       condition.value,
                                                       code.value,
                                                       code2.value,
                                                   ],
                                               )
                                           )
                           return self.Ok(
                               Node("IF", None, {}, [condition.value, code.value])
                           )
       self.i = save
       if self.match("while"):
           self.skip_whitespace()
           condition = self.parse_expression()
           if not condition.failed():
               self.skip_whitespace()
               if self.match("{"):
                   self.skip_whitespace()
                   code = self.parse_block()
                   if not code.failed():
                       self.skip_whitespace()
                       if self.match("}"):
                           return self.Ok(
                               Node("WHILE", None, {}, [condition.value, code.value])
                           )
       self.i = save
       result = self.parse_equality()
       return result




   def parse_assignment(self):
       # assignment := ident/index "=" assignment |OR| logic_or
       save = self.i
       skip = True
       while skip:
           skip = False
           ident = self.parse_primary()
           if ident.failed():
               if ident.errored():
                   return ident
               self.i = save
               break
           self.skip_whitespace()
           if not self.match("="):
               self.i = save
               break
           self.skip_whitespace()
           assign = self.parse_assignment()
           if assign.failed():
               if assign.errored():
                   return assign
               self.i = save
               break
           return self.Ok(Node("ASSIGN", None, {}, [ident.value, assign.value]))
       result = self.parse_control()
       return result




   def parse_expression(self):
       save = self.i
       result = self.parse_assignment()
       return result




   def parse_statement(self):
       result = self.parse_expression()
       self.skip_whitespace()
       if self.match(";"):
           return result
       return self.Error("No semicolon")




   def parse_block(self):
       children = []




       while True:
           self.skip_whitespace()




           if self.match("}"):
               self.i -= 1
               break




           stmt = self.parse_statement()
           if stmt.failed():
               return stmt




           children.append(stmt.value)




       return self.Ok(Node("PROGRAM", None, {}, children))




   def parse_program(self):
       children = []




       while True:
           self.skip_whitespace()
           if self.is_end():
               break




           result = self.parse_statement()




           if result.failed():
               return result




           children.append(result.value)




       return self.Ok(Node("PROGRAM", None, {}, children))








class Api:
   def __init__(self, context):
       self.context = context




   def call(self, function, params):
       name = function
       args = params
       if name.type == "python-function":
           return name.value(*args)
       else:
           backup = self.context.env.copy()
           self.context.env = name.value.env + [{}]
           params = {k: v for k, v in zip(name.value.params, args)}
           self.context.env[-1].update(params)
           res = self.context.execute(name.value.code)
           self.context.env = backup
           return res




   def get(self, var):
       return self.context.get(var)








class Interpreter:
   def __init__(self, ast):
       self.ast = ast
       self.env = [{}]
       self.env[0].update({
           "print": Value(
               "python-function", Object({"pyfunc": self.print_value, "env": [{}]})
           ),
           "input": Value(
               "python-function",
               Object(
                   {
                       "pyfunc": (lambda env: make_string(self, input())),
                       "env": [{}],
                   }
               ),
           ),
           "with": Value(
               "python-function",
               Object({"pyfunc": (lambda env, x: self.with_(x)), "env": [{}]}),
           ),
           "len": Value(
               "python-function",
               Object({"pyfunc": (lambda env, x: make_number(self, len(get_value(x)))), "env":[{}]}),
           ),
           "extend": Value(
               "python-function",
               Object({"pyfunc": self.extend, "env":[{}]}),
           ),
           "contract": Value(
               "python-function",
               Object({"pyfunc": self.contract, "env":[{}]}),
           ),
           "nothing": Value("nothing", Object({})),
           "false": make_boolean(self, False),
           "true": make_boolean(self, True),
       })
   def raw(self, x):
       if not isinstance(x, Value):
           return True
       return False
   def extend(self, env, list_, item):
       list_.value.env["value"].append(item)
       return list_
   def contract(self, env, list_):
       list_.value.env["value"].pop()
       return list_
   def print_value(self, env, x):
       func = x.value.env.get("__repr")
       if func:
           print(self.call(func, []), end="")
       else:
           print(f"<object '{x.type}'>", end="")
       return Value("nothing", Object({}))




   def run(self):
       return self.execute(self.ast)




   def with_(self, file):
       if get_string_value(file).endswith(".yakl"):
           fi = get_file(get_string_value(file))
           p = Parser(fi)
           root = p.parse_program().value
           i = Interpreter(root)
           return i.run()
       else:
           fi = import_python_file(get_string_value(file))
           api = Api(self)
           return fi.load(api)




   def get(self, name):
       x = len(self.env) - 1
       while x >= 0:
           if name in self.env[x]:
               if self.raw(self.env[x][name]): return Value("python-object", Object({}))
               return self.env[x][name]
           x -= 1
       self.env[-1][name] = Value("nothing", Object({}))
       return self.env[-1][name]




   def set_(self, x, y):
       x.type = y.type
       x.value = y.value




   def pycall(self, func, args):
       backup = self.env.copy()
       self.env = func.value.env["env"] + [{}]
       params = {k: v for k, v in zip(func.value.env["params"], args)}
       self.env[-1].update(params)
       res = self.execute(func.value.env["code"])
       self.env = backup
       return res




   def call(self, func, params):
       if func.type == "python-function":
           return func.value.env["pyfunc"](func.value.env["env"], *params)
       else:
           return self.call(func.value.env["__call"], params)




   def execute(self, ast):
       if ast.kind == "PROGRAM":
           last = Value("nothing", Object({}))
           for c in ast.children:
               last = self.execute(c)
           return last
       elif ast.kind == "NUMBER":
           return make_number(self, ast.value)
       elif ast.kind == "STRING":
           return make_string(self, ast.value)
       elif ast.kind == "LIST":
           return Value(
               "list",
               Object({i: self.execute(c) for i, c in enumerate(ast.children[0].children)}),
           )
       elif ast.kind == "ASSIGN":
           val = self.execute(ast.children[1])
           self.set_(self.execute(ast.children[0]), val)
           return val
       elif ast.kind == "IDENT":
           return self.get(ast.value)
       elif ast.kind == "ADD":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__add")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __add")
       elif ast.kind == "SUB":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__sub")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __sub")
       elif ast.kind == "MUL":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__mul")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __mul")
       elif ast.kind == "DIV":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__div")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __div")
       elif ast.kind == "EQU":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__equ")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __equ")
       elif ast.kind == "NEQ":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__neq")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __neq")
       elif ast.kind == "GRE":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__gre")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __gre")
       elif ast.kind == "LES":
           left = self.execute(ast.children[0])
           right = self.execute(ast.children[1])
           func = left.value.env.get("__les")
           if func:
               return self.call(func, [right])
           else:
               raise AttributeError("No __les")
       elif ast.kind == "FUNC":
           return make_function(self, [c.value for c in ast.children[0].children], ast.children[1])
       elif ast.kind == "CALL":
           name = self.execute(ast.children[0])
           args = [self.execute(c) for c in ast.children[1].children]
           return self.call(name, args)
       elif ast.kind == "INDEX":
           name = self.execute(ast.children[0])
           index = self.execute(ast.children[1])
           value =  (
               name.value.env[get_value(index)]
           )
           if self.raw(value): return Value("python-object", Object({}))
           return value
       elif ast.kind == "IF":
           condition = self.execute(ast.children[0])
           if condition.value.env["value"]:
               code = self.execute(ast.children[1])
               return code
           elif len(ast.children) > 2:
               code2 = self.execute(ast.children[2])
               return code2
           return Value("nothing", Object({}))
       elif ast.kind == "WHILE":
           code = Value("nothing", Object({}))
           while self.execute(ast.children[0]).value.env["value"]:
               code = self.execute(ast.children[1])
           return code
       elif ast.kind == "OBJ":
           obj_scope = {}
           self.env.append(obj_scope)
           obj_scope["this"] = Value("object", Object(obj_scope))
           self.execute(ast.children[0])
           self.env.pop()
           return obj_scope["this"]








p = Parser(code)
result = p.parse_program()
if not result.failed():
   i = Interpreter(result.value)
   i.run()
else:
   print(result.value, result.ok, result.backtrack, result.message, result.index)
