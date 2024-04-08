# Stephanie Taylor
# run with Python 3
# Written Fall 2023 for CS232
# Animate a simulation on a DE0 board

import tkinter as tk
import vcd_parser
import sys

#off_hex_colors = ["pink","gray","blue","yellow","cyan","purple","green"]
off_hex_colors = ["gray"] * 7

# Class to store information for a mapping from a bit in a variable to
# a widget in the canvas.
class BitMapping:
    def __init__( self, id, name, bit_idx, widget_name, widget_idx1, widget_idx2 ):
        self.id = id # id in the vcd file
        self.name = name # name from vhd file
        self.bit_idx = bit_idx
        self.widget_name = widget_name # hex, ledr, lredg, sw, or key
        self.widget_idx1 = widget_idx1 # which y7-seg display or which button, or which light, or which switch
        self.widget_idx2 = widget_idx2 # which segment
        
    def __str__(self):
        ret = self.id + " " + self.name + " " + str(self.bit_idx) + "(" + widget_name + "[" + str(self.widget_idx1) + "]"
        if self.widget_idx2 is not None:
            ret += "[" + str(self.widget_idx2) + "]"
        return ret
        
# create a class to build and manage the display application
class DisplayApp:

    # init function
    def __init__(self, vcd_fn, mapping_fn):

        self.paused = True
        self.frame_idx = 0
        self.vcd = vcd_parser.VCD()
        self.vcd.parse_file( vcd_fn )
        self.mapping = self.read_mapping_file( mapping_fn )

        # create a tk object, which is the root window
        self.root = tk.Tk()

        # width and height of the window
        self.initDx = 380+40
        self.initDy = 400

        # set up the geometry for the window
        self.root.geometry( "%dx%d+50+30" % (self.initDx, self.initDy) )

        # set the title of the window
        parts = vcd_fn.split('.vcd')
        parts = parts[0].split('/')
        self.root.title("VCD Board Movie: "+parts[-1])

        # set the maximum size of the window for resizing
        self.root.maxsize( 1024, 768 )

        # bring the window to the front
        self.root.lift()

        # setup the menus
        self.buildMenus()

        # build the Canvas and the timeline canvas
        self.buildCanvas()
               
        # build the controls
        self.buildControls()

        # add objects to the canvas
        self.buildBoard() 
        self.updateBoardDrawing()
        
    def buildMenus(self):
        pass
        
    # create the canvas object
    def buildCanvas(self):
        # this makes the canvas the same size as the window, but it could be smaller
        self.canvas = tk.Canvas( self.root, width=self.initDx, height=self.initDy-175 )
        self.canvas.pack( side=tk.TOP, expand=tk.YES )#expand=tk.YES, fill=tk.BOTH )
        # make a separator line
        sep = tk.Frame( self.root, height=2, width=self.initDx, bd=1, relief=tk.SUNKEN )
        sep.pack( side=tk.TOP, padx = 2, pady = 2, fill=tk.X)
        # Then a canvas for the timeline
        self.timelineCanvas =  tk.Canvas( self.root, width=self.initDx, height=65 )
        self.timelineCanvas.pack(side=tk.TOP, padx=2, pady=2, fill=tk.X, expand=tk.YES)
        return

    # build a frame and put controls in it
    def buildControls(self):
        # make a separator line
        sep = tk.Frame( self.root, height=2, width=self.initDx, bd=1, relief=tk.SUNKEN )
        sep.pack( side=tk.TOP, padx = 2, pady = 2, fill=tk.X)

        # make a control frame
        self.cntlframe = tk.Frame(self.root, width=self.initDx, height=95)
        self.cntlframe.pack(side=tk.TOP, padx=5, fill=tk.X, expand=tk.YES)

        # make Start and Pause buttons in the frame
        self.startButton = tk.Button( self.cntlframe, text="Start", command=self.handleStartButton, width=6 )
        self.pauseButton = tk.Button( self.cntlframe, text="Pause", command=self.handlePauseButton, width=6 )
        self.resetButton = tk.Button( self.cntlframe, text="Reset", command=self.handleResetButton, width=6 )
        self.startButton.pack(side=tk.LEFT)  # default side is top
        self.pauseButton.pack(side=tk.LEFT)  # default side is top
        self.resetButton.pack(side=tk.LEFT)
        self.speedScale = tk.Scale( self.cntlframe, from_=0.5, to=10, resolution=0.1, command=self.handleSlider, orient=tk.HORIZONTAL, label="Speed (steps/s)" )
        self.quickscale = 1 
        self.speedScale.set(self.quickscale) 
        self.speedScale.pack(side=tk.LEFT, expand=tk.YES)
#         tk.Label( self.cntlframe, text="Speed\n(steps/s)" ).pack(side=tk.TOP)

    def handleStartButton(self):
        self.paused = False
        self.animate()
    
    def handlePauseButton(self):
        self.paused = True
        
    def handleResetButton(self):
        self.frame_idx = 0
        self.updateBoardValues()
        self.updateBoardDrawing()
        
    def handleSlider(self, value):
        self.quickscale = float(value)

    def read_mapping_file( self, fn ):
        """ Parse the bit-mapping file to connect widgets to
        bits within top-scope variables
        """
        f = open( fn, 'r' )
        lines = f.readlines()
        f.close()
        mapping = [] # list of BitMappings
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == '#':
                # The line is just a comment
                continue
            parts = line.split(',')      
            name = parts[0].strip()
            found = False
            total_bits = None
            for id in self.vcd.top_scope_ids:
                var_def = self.vcd.variable_definitions[id]
                if var_def.is_named( name ):
                    found =True
                    total_bits = var_def.bitwidth
                    break
            if not found:
                print( "Failed to find variable ", name,"at top scope" )
            bit_idx = int(parts[1].strip())
            widget_name = parts[2].strip().lower()
            widget_idx1 = int(parts[3].strip())
            if len(parts) > 4:
                widget_idx2 = int(parts[4].strip())
            else:
                widget_idx2 = None
            bm = BitMapping( id, name, bit_idx, widget_name, widget_idx1, widget_idx2 )
            mapping.append( bm )
        return mapping
        
    def build7Seg(self,x0,y0):
        segments = [0]*7
        seg_thick = 5;
        seg_length = 20;
        gap = 2
        segments[0] = self.canvas.create_rectangle( x0+gap+seg_thick, y0, x0+gap+seg_length+seg_thick, y0+seg_thick, fill=off_hex_colors[0] )
        segments[1] = self.canvas.create_rectangle( x0+seg_length+2*gap+seg_thick, y0+seg_thick+gap, x0+seg_length+2*gap+seg_thick+seg_thick, y0+seg_thick+gap+seg_length, fill=off_hex_colors[1] )
        segments[2] = self.canvas.create_rectangle( x0+seg_length+2*gap+seg_thick, y0+2*seg_thick+3*gap+seg_length, x0+seg_length+2*gap+seg_thick+seg_thick, y0+2*seg_thick+3*gap+seg_length*2, fill=off_hex_colors[2] )
        segments[6] = self.canvas.create_rectangle( x0+gap+seg_thick, y0+gap+seg_thick+gap+seg_length, x0+gap+seg_length+seg_thick, y0+gap+seg_thick+gap+seg_length+seg_thick, fill=off_hex_colors[6] )
        segments[3] = self.canvas.create_rectangle( x0+gap+seg_thick, y0+gap+2*seg_thick+3*gap+2*seg_length, x0+gap+seg_length+seg_thick, y0+gap+2*seg_thick+3*gap+2*seg_length+seg_thick, fill=off_hex_colors[3] )
        segments[5] = self.canvas.create_rectangle( x0, y0+seg_thick+gap, x0+seg_thick, y0+seg_thick+gap+seg_length, fill=off_hex_colors[5] )
        segments[4] = self.canvas.create_rectangle( x0, y0+2*seg_thick+3*gap+seg_length, x0+seg_thick, y0+2*seg_thick+3*gap+seg_length*2, fill=off_hex_colors[4] )
        
        return segments
        
    def buildBoard(self):
        if self.vcd is None:
            return
        self.canvas.delete(tk.ALL)
        self.canvas.create_rectangle( 20, 20, 200, 93, fill="gray" )
        self.hex_displays = [0,0,0,0]
        self.hex_displays[0] = self.build7Seg( 160, 25 )
        self.canvas.create_text( 180, 105, text="Hex0" ) 
        self.hex_displays[1] = self.build7Seg( 115, 25 )
        self.canvas.create_text( 134, 105, text="Hex1" ) 
        self.hex_displays[2] = self.build7Seg( 70, 25 )
        self.canvas.create_text( 89, 105, text="Hex2" ) 
        self.hex_displays[3] = self.build7Seg( 25, 25 )
        self.canvas.create_text( 42, 105, text="Hex3" ) 
        self.hex_display_values = [['1','1','1','1','1','1','1'],['1','1','1','1','1','1','1'],['1','1','1','1','1','1','1'],['1','1','1','1','1','1','1']]
        
        self.gled_values = ['0','0','0','0','0','0','0','0','0','0']
        self.gleds = []
        for i in range(10):
            self.gleds.append( self.canvas.create_rectangle(380-i*18,85,380-(i-1)*18-5,95,fill="white",outline="green") )
            self.canvas.create_text( 380-i*18+7,105,text=int(i) )
                        
        self.switch_values = ['0','0','0','0','0','0','0','0','0','0']
        self.switch_bottoms = []
        self.switch_tops = []
        for i in range(10):
            self.switch_bottoms.append( self.canvas.create_rectangle(260-i*26,165,260-(i-1)*26-5,190,fill="black",outline="black") )
            self.switch_tops.append( self.canvas.create_rectangle(260-i*26,140,260-(i-1)*26-5,165,fill="white",outline="black") )
            self.canvas.create_text( 260-i*26+12,200,text=int(i) )
            
        self.key_button_values = ['1','1','1']
        self.key_buttons = []
        for i in range(3):
            self.key_buttons.append( self.canvas.create_oval(370-i*30,165,370-(i-1)*30-5,190,fill="white",outline="black") )
            self.canvas.create_text( 370-i*30+15, 200, text="B"+str(i) )
           
        self.timeStartX = 20
        self.timeStopX = 390
        base = 30
        self.timelineCanvas.create_rectangle( self.timeStartX, base, self.timeStopX, base+5, fill="black" )
        if self.vcd is not None and len(self.vcd.timesteps) < 30:
            step = (self.timeStopX-self.timeStartX)/(len(self.vcd.timesteps)-1)
            for i in range(len(self.vcd.timesteps)):
                self.timelineCanvas.create_rectangle( self.timeStartX+step*i-1, base-5, self.timeStartX+step*i+1, base+5, fill="black" )
      
        self.timelineCanvas.create_text( 192, base+30, text="Time Steps" ) 
        self.timeMarker = self.timelineCanvas.create_rectangle(self.timeStartX-1,base-5,self.timeStartX+1,base+15,fill="red") 
        
    def updateBoardDrawing(self):
        """ Update the widgets themselves, based on their values
        """
        for hex_idx in range(4):
            for seg_idx in range(7):
                if self.hex_display_values[hex_idx][seg_idx] == '0':
                    self.canvas.itemconfig( self.hex_displays[hex_idx][seg_idx], fill='orange' )
                else:
                    self.canvas.itemconfig( self.hex_displays[hex_idx][seg_idx], fill=off_hex_colors[seg_idx] )
        for idx in range(10):
            if self.gled_values[idx] == '1':
                self.canvas.itemconfig( self.gleds[idx], fill="green" )
            else:
                self.canvas.itemconfig( self.gleds[idx], fill="white" )
        for idx in range(10):
            if self.switch_values[idx] == '1':
                self.canvas.itemconfig( self.switch_bottoms[idx], fill="white" )
                self.canvas.itemconfig( self.switch_tops[idx], fill="black" )
            else:
                self.canvas.itemconfig( self.switch_bottoms[idx], fill="black" )
                self.canvas.itemconfig( self.switch_tops[idx], fill="white" )
        for idx in range(3):
            if self.key_button_values[idx] == '0':
                self.canvas.itemconfig( self.key_buttons[idx], fill="black" )
            else:
                self.canvas.itemconfig( self.key_buttons[idx], fill="white" )
 
        if self.vcd is not None:
            base = 30
            newX = self.timeStartX+int(float(self.frame_idx)/(len(self.vcd.timesteps)-1)*(self.timeStopX-self.timeStartX))
            self.timelineCanvas.coords( self.timeMarker, newX-1, base-5, newX+1, base+15 )

    def updateBoardValues(self):
        """ Update the values of all the widgets on the board, based on
        the variable changes
        """
        if self.vcd is None:
            return
        if self.frame_idx >= len(self.vcd.variable_changes):
            return
        for id in self.vcd.variable_changes[self.frame_idx]:
            var = self.vcd.variable_changes[self.frame_idx][id] # a Variable (just id and value)
            # this id may show up in more than one mapping. so make sure we update
            # each widget that it is mapped to
            for bm in self.mapping:
                if bm.id != id:
                    # this isn't one we are tracking
                    continue
                if bm.widget_name == 'hex':
                    self.hex_display_values[bm.widget_idx1][bm.widget_idx2] = var.get_bit(bm.bit_idx)
                elif bm.widget_name == 'ledg':
                    self.gled_values[bm.widget_idx1] = var.get_bit(bm.bit_idx)
                elif bm.widget_name == 'button':
                    self.key_button_values[bm.widget_idx1] = var.get_bit(bm.bit_idx)
                elif bm.widget_name == 'switch':
                    self.switch_values[bm.widget_idx1] = var.get_bit(bm.bit_idx)
        
    def animate(self):
        """ This needs to be recursive because the pause is not blocking
        """ 
        if not self.paused and self.frame_idx < len(self.vcd.timesteps):
            self.updateBoardValues()
            self.updateBoardDrawing()
            self.frame_idx += 1
            self.root.after( int(1000.0/self.quickscale), self.animate )
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print( "Usage: python vcd_movie.py <vcd_filename> <mapping_filename>" )
        print( "  e.g. python vcd_movie.py lab01/testbench.vcd lab01/testbench_mapping.txt" )
        sys.exit()

    vcd_fn = sys.argv[1]
    map_fn = sys.argv[2]
    d = DisplayApp(vcd_fn,map_fn)
    d.root.mainloop()