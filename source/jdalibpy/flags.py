#! /usr/bin/python3.4

"""Command-line flag parsing utilities."""
# Jonathan Aldrich 2016-04-28

class FlagMismatchError(Exception):
    def __init__(self, message=""):
        self.message = message

class FlagParseError(Exception):
    def __init__(self, message=""):
        self.message = message

class Flags:
    """Contains definitions and values for command-line flags."""

    def __init__(self):
        self.flag_defs = {}
        self.flag_vals = {}
    
    def __del__(self):
        pass
        
    def DefineFlag(self, flag_name, value_type = "string", default_value = None):
        self.flag_defs[flag_name] = value_type
        if default_value is not None:
            self.flag_vals[flag_name] = default_value
            
    def DefineInt(self, flag_name, default_value = None):
        self.DefineFlag(flag_name, "int", default_value)
            
    def DefineFloat(self, flag_name, default_value = None):
        self.DefineFlag(flag_name, "float", default_value)
            
    def DefineBool(self, flag_name, default_value = None):
        self.DefineFlag(flag_name, "bool", default_value)
            
    def DefineString(self, flag_name, default_value = None):
        self.DefineFlag(flag_name, "string", default_value)
            
    def SetFlag(self, flag_name, value):
        if flag_name in self.flag_defs:
            t = self.flag_defs[flag_name]
            if t == "int":
                try:
                    val = int(value, 0)
                    self.flag_vals[flag_name] = val
                except:
                    raise FlagMismatchError("Flag %s != int: %s" % (flag_name, value))
            elif t == "float":
                try:
                    self.flag_vals[flag_name] = float(value)
                except:
                    raise FlagMismatchError("Flag %s != float: %s" % (flag_name, value))
            elif t == "bool":
                try:
                    self.flag_vals[flag_name] = bool(value)
                except:
                    raise FlagMismatchError("Flag %s != bool: %s" % (flag_name, value))
            else:  # string
                self.flag_vals[flag_name] = value
        else:
            FlagParseError("Flag %s not found." % flag_name)
    
    def GetFlag(self, flag_name):
        return self.flag_vals[flag_name] if flag_name in self.flag_vals else None
        
    def HasFlag(self, flag_name):
        return flag_name in self.flag_vals
        
    def ListFlags(self):
        return str(self.flag_defs)
        
    def ListFlagValues(self):
        return str(self.flag_vals)

    def ParseFlags(self, argv):
        ret_argc = 0
        ret_argv = []
        flag_name = ""
        for arg in argv:
            if flag_name:
                self.SetFlag(flag_name, arg)
                flag_name = ""
            elif arg[:2] == "--":
                eq = arg.find("=")
                if eq != -1:
                    self.SetFlag(arg[2:eq], arg[eq+1:])
                else:
                    flag_name = arg[2:]
                    if flag_name in self.flag_defs:
                        if self.flag_defs[flag_name] == "bool":
                            self.SetFlag(flag_name, True)
                            flag_name = ""
                    elif (flag_name[:2] == "no" and flag_name[2:] in self.flag_defs
                        and self.flag_defs[flag_name[2:]] == "bool"):
                        self.SetFlag(flag_name[2:], False)
                        flag_name = ""
            else:
                ret_argc += 1
                ret_argv.append(arg)
        if flag_name:
            raise FlagParseError("Flag %s has no value." % flag_name)
        return (ret_argc, ret_argv)