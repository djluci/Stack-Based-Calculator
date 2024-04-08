# Stephanie Taylor
# Fall 2020, updated Fall 2023
# Code to parse VCD files generated in CS232
# Run with Python 3

import sys

class VariableDefinition:
    def __init__( self, var_type, bitwidth, id, name, scope ):
        self.var_type = var_type
        self.bitwidth = bitwidth
        self.id = id
        self.name = name
        self.scope = scope[:]
        self.scope_name = "/".join(self.scope)
        
    def is_named( self, name ):
        """ return true if the variable has the given name.
        This means we need to strip away any indices.
        """
        if self.name.lower() == name.lower():
            return True
        parts = self.name.split( '[' )
        return parts[0].lower() == name.lower()
    
    def __str__( self ):
        return self.scope_name + " " + self.name + " (" + self.id + ", " + str(self.bitwidth) + ")"
        
class Variable:
    def __init__( self, id, value ):
        self.id = id
        self.value = value
        
    def get_bit( self, idx ):
        """ If the value has just one bit, the return it
        If it starts with a b and has more than one bit, then
        then the bit at idx 0 is the rightmost bit
        """
        if self.value[0] == 'b':
            return self.value[len(self.value)-1-idx]
        else:
            if len(self.value) != 1:
                print( "The value of variable with id", self.id, "should be of length 1, but isn't. It's value is",  self.value )
            return self.value
        
class VCD:
    def __init__( self ):
        self.module_name = ""
        self.timescale = None
        self.variable_definitions = {} # the dictionary of variable definitions (id is key)
        self.timesteps = [] # one time value per timestep
        self.variable_changes = [] # one dictionary of variables per time step (id is key)
        self.scope_names = [] # list of the scopes. each scope is a string
        self.top_scope_ids = [] # list of ids of variables in the top scope
        
    def print_variableDefinitions(self):
        for id in self.variable_definitions:
            print( str(self.variable_definitions[id]) )
            
    def get_top_scope( self ):
        """ Some of the vcd files that Stephanie has have a top scope with
        the name of the module. Others have no name for the top scope.
        Figure out which one this is.
        """
        blank = ''
        module = "/module." + self.module_name
        found_blank = 0
        found_module = 0
        for var_def in self.variable_definitions.values():
            if var_def.scope_name == blank:
                found_blank += 1
            if var_def.scope_name.lower() == module.lower():
                found_module += 1
        #if found_blank > 0:
        #   print( "found variables in blank scope"  )
        #if found_module > 0:
        #    print( "found variable in module scope" )
        if found_blank > 0:
            if found_module > 0:
                print( "Not sure what top scope is because we found variables in un-named scope and module scope" )
                sys.exit()
            return blank
        if found_module > 0:
            return module
            
    def sequester_variables_in_top_scope( self ):
        sn = self.get_top_scope()
        self.top_scope_ids = []
        for id in self.variable_definitions:
            var_def = self.variable_definitions[id]
            if var_def.scope_name.lower() == sn.lower():
                self.top_scope_ids.append( id )
        
    def legal( self, id, value ):
        """ Return true if there is a variable with this id and the value
             has the right number of bits.
        """
        if id not in self.variable_definitions:
            return False
        if value[0] == 'b':
            numbits = len(value)-1
        else:
            numbits = len(value)
        var_def = self.variable_definitions[id]
        return var_def.bitwidth == numbits
        
    def parse_file( self, filename ):
        parts = filename.split('/')
        parts = parts[-1].split('.vcd')
        self.module_name = parts[0]
        fobj = open( filename, 'rU' )
        lines = fobj.readlines()
        if len(lines) == 1:
            print( "huh?" )
            sys.exit()
        for lidx in range(len(lines)):
            line = lines[lidx].strip()
            if "$timescale" in line and line.index("$timescale") == 0:
                # maybe the info is all on one line
                words = line.split()
                if len(words) > 1:
                    self.timescale = words[1]
                    startAt = lidx+1;
                else:
                    # or maybe it is on separate lines. allow up to 5 empty lines.
                    for offset in range(5):
                        line = lines[lidx+offset].strip()
                        if len(line) > 0:
                            self.timescale = line.split()[0]
                            startAt = lidx + offset + 1
                            break
                break
        # search for all variable definitions, keeping track of nested scope.
        current_scope = [""]
        current_scope_name = ""
        self.scope_names = [current_scope_name]
        for lidx in range(startAt, len(lines)):
            line = lines[lidx].strip()
            # we are at the end of the definitions
            if len(line) > len("$enddefinitions") and line[:len("$enddefinitions")] == "$enddefinitions":
                startAt = lidx + 1
                break
            # we are defining a new scope
            if len(line) > len("$scope") and line[:len("$scope")] == "$scope":
                words = line.split()
                if len(words) < 2 or words[-1] != "$end":
                    print( "Unexpected scope line", lidx, ": ", line )
                    sys.exit()
                current_scope.append( ".".join(words[1:-1]) )
                current_scope_name = "/".join(current_scope) 
                if current_scope_name not in self.scope_names:
                    self.scope_names.append( current_scope_name )
            # We are leaving the nested scope
            if len(line) > len("$upscope") and line[:len("$upscope")] == "$upscope":
                words = line.split()
                if len(words) != 2 or words[-1] != "$end":
                    print( "Unexpected upscope line", lidx, ": ", line )
                    sys.exit()
                current_scope.pop()
         
            # A variable definition line has the format
            # $var type bitwidth id name $end
            words = line.split()
            if words[0] == "$var":
                id = words[3]
                self.variable_definitions[id] = VariableDefinition( var_type=words[1], bitwidth=int(words[2]), id=id, name=words[4], scope=current_scope )
                
        # Now look for the variable change section to begin. Look for the first timestep, which
        # will be a line that has a hashtag and number only.
        for lidx in range(startAt, len(lines)):
            line = lines[lidx].strip()
            if len(line) > 0 and line[0] == "#" and line[1:].isdigit():
                startAt = lidx
                break
                
        self.timesteps = [line] # found our first time step
        self.variable_changes = [{}] # but no variables yet
        for lidx in range(startAt+1,len(lines)):
            line = lines[lidx].strip()
            if len(line) > 0 and line[0] == "#" and line[1:].isdigit():
                # start a new timestep
                self.timesteps.append( line )
                self.variable_changes.append( {})
            else:
                # split up the values and the ids this is easy if they 
                # are separated by spaces.
                words = line.split()
                if len(words) == 2:
                    var = Variable( id=words[1], value=words[0] )
                else:
                    # the first characters are the value.
                    # the last character or characters are the id.
                    var = None
                    for splitPoint in range(-1,-len(line),-1):
                        id = line[splitPoint:]
                        value = line[:splitPoint]
                        #print( splitPoint, id, value )
                        if self.legal( id, value ):
                            var = Variable( id = id, value = value )
                    if var is None:
                        print( "Failed to separate value from id for line", lidx, ": ", line )
                        sys.exit()
                self.variable_changes[-1][var.id] = var
        self.sequester_variables_in_top_scope()
        
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    vcd = VCD()
    # There files were sort of randomly collected. I have no idea if the answers are correct. Some are from student files. I just grabbed one version for every filename.
    #vcd.parse_file( "adder.vcd" )
    #vcd.parse_file( "addsubtest.vcd" )
    #vcd.parse_file( "alutestbench.vcd" )
    #vcd.parse_file( "boxtest.vcd" )
    #vcd.parse_file( "brighttest.vcd" )
    #vcd.parse_file( "calcbench.vcd" )
    #vcd.parse_file( "cpubench.vcd" )
    #vcd.parse_file( "extensiontest.vcd" )
    #vcd.parse_file( "fourastest.vcd" )
    #vcd.parse_file( "hexbench.vcd" )
    #vcd.parse_file( "lightsbench.vcd" )
    #vcd.parse_file( "pldbench.vcd" )
    #vcd.parse_file( "ramromtester.vcd" )
    #vcd.parse_file( "stackertest.vcd" )
    #vcd.parse_file( "lab01/testbench.vcd" )
    #vcd.parse_file( "trafficbench.vcd" )
    vcd.parse_file( filename )
    print( "top level variable names" )
    vcd.print_variableDefinitions()
    print( "scope names", vcd.scope_names )
    print( "module name", vcd.module_name )
    print( "time steps", vcd.timesteps )   
 
    print( "top level variables: ");
    for id in vcd.top_scope_ids:
        print( vcd.variable_definitions[id] )
    print("top scope name" );
    print( vcd.get_top_scope() )
        
    #for vc in vcd.variable_changes:
    #    print vc
    