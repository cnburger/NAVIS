#Importing Libraries ------------------------------------------
import pandas as pd
import numpy as np
import math

#for delays
import time
from datetime import datetime

#Import for PostgreSQL functionality
import sqlalchemy
from sqlalchemy import create_engine
import psycopg2

#Imports for basemap and plots
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
from matplotlib.lines import Line2D #for the legend
import datetime #to save files

#Imports for GUI
import tkinter as tk
from tkinter import ttk
from tkinter import ttk
from tkinter import *
import tkinter.font as font
from PIL import Image, ImageTk

matplotlib.use("TkAgg") #backend of matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg , NavigationToolbar2Tk
from matplotlib.figure import Figure


#The following code will allow for retrieving images in the folders
import os
CURRENT_DIRECTORY = str(os.path.dirname(sys.argv[0])) #to het the direcotry to save images & videos
IMAGE_DIRECTORY = CURRENT_DIRECTORY + str("\\Images\\")
VIDEO_DIRECTORY = CURRENT_DIRECTORY + str("\\Videos\\")
VIDEO_WRITER_EXECUTABLE = CURRENT_DIRECTORY + str("\\ffmpeg\\bin\\ffmpeg.exe")
#An image can be refrenced by IMAGE_DIRECTORY+ str(image name) eg. str("ship_display.ico")

#The folowing code is for saving plot video output
plt.rcParams['animation.ffmpeg_path'] = VIDEO_WRITER_EXECUTABLE #for saving a video
Writer = animation.writers['ffmpeg']
writer = Writer(metadata=dict(artist='CNBurger', extra_args = [ '-c:v libx264 -crf 17 -tune film']), bitrate=10000)

#------------------------Constants Declared----------------
#Fonts
HEADING_FONT = ("Century Gothic",30, "bold underline") #font type, size, settings
LABEL_FONT = ("Century Gothic",14)
ENTRY_FONT = ("Century Gothic",14)

#Spacing around GUI buttons and labels
BUTTON_PADX = 5
BUTTON_PADY = 5
#Background colour of all the winodws
BACKGROUND_COLOUR = '#607D8B'

#Database inputs - GLOBAL VARIABLES
database_username = ""
database_password = ""
database_ip = ""
database_name = ""
database_table = ""

#CONSTANTS of vessel statistics
mmsi_entry = 0 #for the MMSI
#The following three lines are here for future datasets if we have the name, dimentions and type of vessel
vesselName = "Not Supported yet"
vesselDim = "Not Supported yet"
vesselType = "Not Supported yet"
vesselLong_min = 0
vesselLong_max = 0
vesselLat_max = 0
vesselLat_min = 0
vesselMaxSpeed = 0
vesselAVG_SOG =  ""
vesselAVG_SOG_LargerZero = ""
vessel_observations =  ""
vessel_stationary =  ""

#PANDAS DATAFRAMES for plotting, will be initiated in the query class, used in animate function
df_Longitude = 0
df_Latitude = 0
df_SOG = 0
df_NAV_status = 0 #navigational status
df_vessel_time = 0
df_COG = 0 #course over ground dataframe

####------------------END OF CONSTANTS AND GLOBAL VARIABLES---------------------
"""
Some acronyms used in the code:
btn_ = button
lbl_ = label
grid_ = Combobox
df_ = pandas data frames
lon = longitude
lat = latitude
"""

def readDatabase(query):
    """
    This function will take a string as an input that is the query that will
    be sent to the database for the data that needs to be extracted and returns
    a dataframe of the values specified to be extracted

    PARAMETERS
    ----------
    query: string
        The query that will be sent
    """

    """
    Creating a postgres database connection next with the input global parameters,
    that was entered in the datbase login window that is used all over the
    program

    RETURN:
    -------
    df_query_result: dataFrame
        It will contain the output data of the query
    """

    database_connection = sqlalchemy.create_engine(
    'postgres+psycopg2://{0}:{1}@{2}/{3}'.
        format(database_username, database_password, database_ip, database_name),
        pool_recycle=1, pool_timeout=57600).connect() #connecting to the DataBase

    #Reading the table and getting the query
    df_query_result = pd.read_sql_query(query, database_connection)
    database_connection.close() #close connection to postgres
    return df_query_result #return dataframe

#Constants for Static Colour map
RED_STATIC_PALETTE = [] #100 red colours
BLUE_STATIC_PALETTE = [] #100 blue colours
GREEN_STATIC_PALETTE = [] #100 green colours

def rgb2hex(r,g,b):
    """
    This function takes in integers of RGB = Red, Green, Blue pixels, and
    makes a HEXADECIMAL number for plotting colours of 100 different shades.

    PARAMETERS:
    ----------
    r: int
        Red input amount range 0-254
    g: int
        Green input amount range 0-254
    b: int
        Blue input amount ranger 0-254

    RETURN:
        String, as hex number
    """
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

def initializeStaticPalettes():
    """
    This function is an initialization function, that will set the colour
    palettes for the static maps. It will append the hex values to the empty
    static map coulour palettes.

    There will be made use of custom rgb formulas with log and postition where
    the rgb starts incrementing as seen below in the for loop, it was decided
    this way so that there is a vissible difference in colours

    """
    #Global so that the values change for the global variables
    global RED_STATIC_PALETTE,GREEN_STATIC_PALETTE,BLUE_STATIC_PALETTE

    #Reset the palletes
    RED_STATIC_PALETTE = [] #100 red colours
    BLUE_STATIC_PALETTE = [] #100 blue colours
    GREEN_STATIC_PALETTE = [] #100 green colours

    counter = 150 #end value of the counter, 150 colours will be made
    for i in range(0,counter):
        RED_STATIC_PALETTE.append(rgb2hex((104+i),int(np.log(200+i)), 0))
        GREEN_STATIC_PALETTE.append(rgb2hex(int(np.log(50+i)),(100+i),0))
        BLUE_STATIC_PALETTE.append(rgb2hex(0,20+i,200))

#----POPUP MESSAGE - TKINTER-----
def popMsg(msg):
    """
    This method creates a tkinter window and makes a popup message for the users

    PARAMETERS
    ----------
    msg: str
        The message that should be displayed in the Error popup
    """
    popup = tk.Tk() #creating a tkinter instance

    def leavemini(): #close the mini popup window
        popup.destroy()

    popup.wm_title("!!! ERROR !!!") #Title of tkinter pupup
    #label that will show the input message
    label = ttk.Label(popup,text = msg, font =("Century Gothic",14, "bold"))
    label.configure(anchor='center') #centre the text
    #place the label in the tkinter window
    label.pack(side = 'top', fill = 'x', pady = 10, padx = 20)
    #Creating a button to exit the application
    btn_popExit = ttk.Button(popup, text = 'EXIT', command = leavemini)
    btn_popExit.pack() #place the button
    popup.mainloop() #tkinter code

#####-------Class for the GUI's ------------------------------------------------
class GISVizTool(tk.Tk):
    """
    This class will represent the Visual tool and it contains all the
    initialization functions for all the forms of the application and their settings
    """
    initializeStaticPalettes() #initialize the static colour maps

    def __init__(self, *args,**kwargs):
        #Initialize the class, and functions in the class
            tk.Tk.__init__(self,*args,**kwargs) #initialize tkinter
            #Changing the tkinter Icon to the free to use Shipping vessel
            tk.Tk.iconbitmap(self,default = IMAGE_DIRECTORY+ str("ship_display.ico"))
            tk.Tk.wm_title(self,"NAVIS") #Changing the title of the frame

            #container that we always have in the tkinter app
            container = ttk.Frame(self) #window of an application
            container.grid(row = 0) #placing the container
            container.grid_rowconfigure(0, weight = 1) #weight = which item gets priority
            container.grid_columnconfigure(0, weight = 1)

            #Configuring the background colour:
            self.configure(background = BACKGROUND_COLOUR)
            self.frames = {} #empty dictionary #helps loading different type of windows

            #adding different windows to toggle between them
            for F in (WelcomeScreen,DBLoginPage,VesselStats,PlotFrame,HeatMapFrame,StaticMapFrame):
                frame = F(container,self)
                self.frames[F] = frame
                #pack or grid, grid of the frame
                frame.grid(row = 0, column = 0, sticky = "nsew")

            #Welcome screen
            self.show_frame(WelcomeScreen) #first window to show

#The next function allows for the showing of a new frame/window
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise() #bring to front

###---- Welcome screen ----
class WelcomeScreen(tk.Frame):
    """
    This class is for the welcome screen, the first screen that the user will
    interact with.
    This class will have 3 buttons.
        Button 1:
            Connect to the database
        Button 2:
            Plot static vessel path
            Disabled until the connection to the database is successful
        Button 3:
            Draw a static map of the vessels, with up to 3
            Disabled until the connection to the database is successful
        Button 4:
            Create a heatmap of vessels
            Disabled until the connection to the database is successful
    """
    def __init__(self,parent,controller):

        tk.Frame.__init__(self,parent)#Frame settings

        self.configure(background = BACKGROUND_COLOUR) #Setting background colour
        lbl_welcome= ttk.Label(self,text ="NAVIS",
                            font =PROJ_NAME_FONT,background = BACKGROUND_COLOUR)
        #Dummy label for spacing
        lbl_dummy = ttk.Label(self,text ="             ",
                    font =("Century Gothic",40),background = BACKGROUND_COLOUR)

        def connectDB():
            """
            This function will be run when the user clicks on the connectDB button
            It opens the Database Login window and it enables the disabled buttons,
            the only way the user can return to this welcome screen if the
            database connection is successful or close the program and start start again

            The user can only use the buttons and the Weclome frame once the
            database connection has succseeded
            """
            controller.show_frame(DBLoginPage) #show Database Login screen
            btn_heatMap["state"] = "enabled" #enables button
            btn_ship["state"] = "enabled"
            btn_staticMap["state"] = "enabled"

        #Creating a style: for the buttons, bigger text and size for the buttons
        btn_conf_style = ttk.Style()
        btn_conf_style.configure('Big.TButton', font = ("Century Gothic",18))

        #Declaring button objects
        btn_connectDB = ttk.Button(self,text="Connect to Database", width = 25,
            style = "Big.TButton",command = lambda:  connectDB())#command = funtion to execute

        btn_ship = ttk.Button(self,text="Vessel Animation", width = 25,
        style = "Big.TButton",command = lambda:  controller.show_frame(VesselStats))

        btn_ship["state"] = "disabled" #keep button disabled until DB connection is passed

        btn_heatMap = ttk.Button(self,text="Spatial Distribution Map",
        width = 25,style = "Big.TButton",command = lambda:  controller.show_frame(HeatMapFrame))
        btn_heatMap["state"] = "disabled" #keep button disabled until DB connection is passed

        btn_staticMap = ttk.Button(self,text="Static Map", width = 25,style = "Big.TButton",
        command = lambda:  controller.show_frame(StaticMapFrame)) #command = funtion to execute
        btn_staticMap["state"] = "disabled" #keep button disabled until DB connection is passed

        #Placing the objects on the GUI
        lbl_welcome.grid(row = 0, column = 1, columnspan = 2,pady = 20)
        lbl_welcome.config(anchor = CENTER) #centre the text in a label
        lbl_dummy.grid(row = 1, column = 0)
        btn_connectDB.grid(row = 2, column = 1,
                        padx = BUTTON_PADX, pady = BUTTON_PADY)
        btn_staticMap.grid(row = 3, column = 1,
                        padx = BUTTON_PADX, pady = BUTTON_PADY)
        btn_ship.grid(row = 4, column = 1,
                        padx = BUTTON_PADX, pady = BUTTON_PADY)
        btn_heatMap.grid(row = 5, column = 1,
                        padx = BUTTON_PADX, pady = BUTTON_PADY)

####-------------------------END OF WELCOME SCREEN -----------------------------

def getArrowSize(sog):
    """
    This function is used to calculate the arrow size that indicates the relative
    speed of a vessel with respect to the other vessels. We made use of visual
    inspection to determine this formula.

    PARAMETERS:
        sog: float
            The current speed of a vessel at an obseration
    RERURN:
        float
            The float value will be a large output float in basemap terms to
            allow us to plot a large arrow
    """
    if(sog < 15):
        return ((sog**4)/2)
    elif(sog<30):
        return (25312.5 +(sog**3)/2)
    else: #else keep stable #speedboat speeds
        return (38812.5 +(sog**2)/2)

####----------------------- END OF FUNCTION ------------------------------------


####---------------------- CLASS: Static Map -----------------------------------
class StaticMapFrame(tk.Frame):
    """
    This class will make a static map of a vessel in an area, with the option
    to draw a static map of up to 3 other vessels within a certian radius of
    a vessel.

    The map will have a change in colour as time passes the path a vessel took,
    it will indicate when a vessel has stopped.
    It will indicate the speed and date of a vessel at certian time stamps.
    The marker size will change as the speed of a vessel increased or decreased

    """
    def __init__(self,parent,controller):
        #Frame settings
        tk.Frame.__init__(self,parent)
        self.configure(background = BACKGROUND_COLOUR) #Setting the background colour

        #ALL TKINTER OBJECTS FOR THIS FRAME:
        #Defining label objects
        lbl_static_map_heading = ttk.Label(self,text = "Static Map Generation",
                            font = HEADING_FONT, background = BACKGROUND_COLOUR)
        lbl_MMSI =  ttk.Label(self,text ="Enter Vessel MMSI:", font =LABEL_FONT,
                            background = BACKGROUND_COLOUR)
        lbl_MMSI_Other =  ttk.Label(self,text ="MMSI's to include:", font =LABEL_FONT,
                            background = BACKGROUND_COLOUR)
        lbl_dummy = ttk.Label(self,text ="    ",
                            font =("Century Gothic",40),background = BACKGROUND_COLOUR)
        lbl_dummy_2 = ttk.Label(self,text ="       ",
                            font =("Century Gothic",20),background = BACKGROUND_COLOUR)
        lbl_Quality =  ttk.Label(self,text ="Quality of plot:",
                            font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        lbl_Annotation_Settings =  ttk.Label(self,text ="Annotations:",
                            font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        lbl_amt_annotations =  ttk.Label(self,text ="Maximum annotations: ",
                            font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)

        #Defining entry box objects:
        entry_MMSI = ttk.Entry(self,font =ENTRY_FONT)
        entry_MMSI.insert(0,'240985000') #default vessel id

        #Combobox objeccts
        grid_Ship_2= ttk.Combobox(self, font = ENTRY_FONT)
        grid_Ship_2['values']= ("Not Loaded")
        grid_Ship_2["state"] = "disabled"#keeping disabled until mmsi search successful

        grid_Ship_3= ttk.Combobox(self, font = ENTRY_FONT)
        grid_Ship_3['values'] = ("Not Loaded")
        grid_Ship_3["state"] = "disabled"#keeping disabled until mmsi search successful

        #plotting quality
        grid_quality = ttk.Combobox(self, font = ENTRY_FONT)
        grid_quality['values']= ('Low','Intermediate','High','Full (takes time)')
        grid_quality.current(1) #default intermediate
        grid_quality["state"] = "disabled" #keeping disabled until mmsi search successful

        #Amount of annotations
        grid_Annotation_amt = ttk.Combobox(self, font = ENTRY_FONT)
        grid_Annotation_amt['values'] = (np.arange(1,40)).tolist()
        grid_Annotation_amt['state'] = "disabled" #keeping disabled until user wants annotations

        #Defining button objects:
        btn_NAV_STYLE = ttk.Style() #style for nutton
        btn_NAV_STYLE.configure('NAV.TButton', font = ("Century Gothic",11))
        btn_search_MMSI = ttk.Button(self,text="Search", width = 20,
        style = "NAV.TButton",  command = lambda:  searchMMSI_static()) #check if mmsi exists

        #BACK button
        btn_back= ttk.Button(self,text="Back", width = 20, style = 'NAV.TButton',
        command = lambda: controller.show_frame(WelcomeScreen) )

        #Static Plot button
        btn_staticPlot= ttk.Button(self,text="Plot!", width = 20, style = 'NAV.TButton',
        command = lambda: startStaticPlot())
        btn_staticPlot["state"] = "disabled"#keeping disabled until mmsi search successful

        #Declaring Checkbox objects, and variables to know if the checkboxes where selected or not
        chk_ship_2_status = tk.IntVar()
        chk_ship_3_status = tk.IntVar()
        chk_annotation_speed_status = tk.IntVar()
        chk_annotation_status = tk.IntVar()
        chk_annotation_arrow = tk.IntVar()

        chk_ship2 = tk.Checkbutton(self, text="include",  font =  LABEL_FONT ,
                                    bg = BACKGROUND_COLOUR, variable = chk_ship_2_status)
        chk_ship2["state"] = "disabled"#keeping disabled until mmsi search successful

        chk_ship3 = tk.Checkbutton(self, text="include", font =  LABEL_FONT,
                                    bg = BACKGROUND_COLOUR, variable = chk_ship_3_status)
        chk_ship3["state"] = "disabled"#keeping disabled until mmsi search successful

        chk_annotation = tk.Checkbutton(self, text="Include annotations",bg = BACKGROUND_COLOUR,
                            font =  LABEL_FONT, variable = chk_annotation_status,
                            command = lambda: annotationObjectState(chk_annotation_status.get()))
        chk_annotation['state'] = 'disabled'

        chk_annotation_speed = tk.Checkbutton(self, text="Include Marker where SOG < 1",font =  ("Century Gothic",10),
                                bg = BACKGROUND_COLOUR, variable = chk_annotation_speed_status)
        chk_annotation_speed['state'] = "disabled"

        #Creating a checkbox for adding arrows to the plot
        #Arrows will indicae the Course over ground (COG) in degrees as well as the speed
        chk_arrows= tk.Checkbutton(self, text="Indicate COG (course) and SOG (speed) with arrows",
                                font =  ("Century Gothic",10),
                                bg = BACKGROUND_COLOUR, variable = chk_annotation_arrow)
        chk_arrows['state'] = "disabled"

        #Allignmnent of objeccts
        lbl_static_map_heading.configure(anchor = CENTER)
        lbl_dummy.grid(row =1, column = 0)
        lbl_dummy_2.grid(row =3, column = 0)
        lbl_static_map_heading.grid(row = 0, column = 1, columnspan = 6, rowspan = 2)
        lbl_MMSI.grid(row = 2, column = 1 ,padx =BUTTON_PADX, pady = BUTTON_PADY)
        entry_MMSI.grid(row =2, column = 2,padx =BUTTON_PADX, pady = BUTTON_PADY)
        btn_search_MMSI.grid(row = 2, column = 3, padx =BUTTON_PADX, pady = BUTTON_PADY)
        lbl_MMSI_Other.grid(row = 4, column = 1)
        grid_Ship_2.grid(row = 5, column = 2, padx =BUTTON_PADX, pady = BUTTON_PADY)
        chk_ship2.grid(row = 5, column = 3, padx =BUTTON_PADX, pady = BUTTON_PADY)
        chk_ship3.grid(row = 6, column = 3, padx =BUTTON_PADX, pady = BUTTON_PADY)
        grid_Ship_3.grid(row = 6, column = 2, padx =BUTTON_PADX, pady = BUTTON_PADY)
        lbl_Quality.grid(row = 7, column = 1,padx =BUTTON_PADX, pady = BUTTON_PADY)
        grid_quality.grid(row = 7, column = 2, padx =BUTTON_PADX, pady = BUTTON_PADY)
        chk_arrows.grid(row = 8, column = 2,padx =BUTTON_PADX, pady = BUTTON_PADY, columnspan =2)
        lbl_Annotation_Settings.grid(row = 9, column = 1, padx =BUTTON_PADX, pady = BUTTON_PADY)
        chk_annotation.grid(row = 9, column = 2, padx =BUTTON_PADX, pady = BUTTON_PADY)
        lbl_amt_annotations.grid(row = 10, column = 1)
        grid_Annotation_amt.grid(row = 10, column = 2)
        chk_annotation_speed.grid(row = 11, column = 2)
        btn_staticPlot.grid(row = 12, column = 3,padx =BUTTON_PADX, pady = BUTTON_PADY)
        btn_back.grid(row = 13, column = 3,padx =BUTTON_PADX, pady = BUTTON_PADY)


        #Static plot button function
        def startStaticPlot():
            #getting variable values, and setting
            plotQuality = grid_quality.get() #gets plot Quality

            def returnQuery(mmsi):
                """
                This function returns the query that will be sent to the database

                PARAMETERS:
                ----------
                mmsi: string
                    MMSI that needs to be queried

                RETURNS:
                    temp: string
                        This string that is outputted here is the string that
                        will be used to do the query
                """
                temp = str("SELECT ST_X(geom::geometry) as lat, " +
                " ST_Y(geom::geometry) as long, sog, cog, datetimestamp FROM " +database_table +
                " WHERE (MMSI = "+mmsi+ ") ORDER BY datetimestamp ASC")
                return temp

            dataframe_list = []  #creating a list of all the dataframes of different vessels
            df_vessel_1 =  readDatabase(returnQuery(mmsi =entry_MMSI.get())) #get vessel info
            dataframe_list.append(df_vessel_1) #add vessel info to list

            #Create additional possible vessels
            df_vessel_2 = []
            df_vessel_3 = []

            #Min and max list of longitude and latitude to help with the dimentions of basemap
            min_lat = []
            max_lat = []
            min_long = []
            max_long = []

            #Getting the vessel min and max function values
            max_lat.append(max(df_vessel_1['lat']))
            min_lat.append(min(df_vessel_1['lat']))
            min_long.append(min(df_vessel_1['long']))
            max_long.append(max(df_vessel_1['long']))

            #Check the status of a vessel if vessel 2 is selected add information
            if(chk_ship_2_status.get() == 1):
                #Database query:
                df_vessel_2 = readDatabase(returnQuery(mmsi =grid_Ship_2.get()))
                #Ad min max functions
                max_lat.append(max(df_vessel_2['lat']))
                min_lat.append(min(df_vessel_2['lat']))
                min_long.append(min(df_vessel_2['long']))
                max_long.append(max(df_vessel_2['long']))
                #Add dataframe to the list
                dataframe_list.append(df_vessel_2)

            #Check the status of a vessel if vessel 2 is selected add information
            if(chk_ship_3_status.get() == 1):
                #Databse query
                df_vessel_3 = readDatabase(returnQuery(mmsi =grid_Ship_3.get()))
                max_lat.append(max(df_vessel_3['lat']))
                min_lat.append(min(df_vessel_3['lat']))
                min_long.append(min(df_vessel_3['long']))
                max_long.append(max(df_vessel_3['long']))
                #Add dataframe to vessel list
                dataframe_list.append(df_vessel_3)

            #Basemap instuctions
            plt.figure(figsize=(7,7)) # figure size of basemap
            m = Basemap(projection = 'mill',
            llcrnrlon = math.floor(min(min_lat)), #flipping the observations for correct dimentions
            urcrnrlon = math.ceil(max(max_lat)),
            urcrnrlat = math.ceil(max(max_long)),
            llcrnrlat = math.floor(min(min_long)),
            resolution = str(grid_quality.get()[0]).lower())
            """
            floor & ceil is used above to draw a nice border of the plot that
            will be visualized
            """
            #Diffeernet colour palettes for the vessels to be plotted in
            colour_palettes = [BLUE_STATIC_PALETTE, GREEN_STATIC_PALETTE, RED_STATIC_PALETTE]
            #colour palette indicator counter, to denote diffenet colours between different amount of vessels chosen to plot
            col_pal = 0

            def annotateString(speed,course, date_time):
                """
                Converts data types and makes a string for the annotations

                Parameters
                ----------
                speed: float
                    The vessels speed at the specific annotation point
                course: float
                    The heading of the vessel
                date_time: datetime
                    The vessels date and time at a annotation point

                Return:
                    string
                        The string returned is the message that will be displayed
                        in the annotation
                """
                return str("SOG:" +str(speed) + " COG:" + str(round(course))+
                            "\n" + (date_time).strftime('%Y-%m-%d'))


            def annotateInterval(size, amount_anno):
                """
                This function will calculate the interval, at which an annotation shoud be showed
                for example

                7456 observations, and the user wants 13 Annotations
                7456/13 = 573.56 ~ each 573th observation will receive an annotation

                The user will then be able to use modulo (%) to plot an annotation equal amount of times

                Parameters
                ----------
                size: int
                    Size of the dataset (total amnt of obervations)
                amount_anno: int
                    The amount of annotations that the user wants

                """
                return int(math.floor(size/amount_anno)) #floor to get rid of decimals

            #BBox is for the annotation style
            bbox = dict(boxstyle = "round", fc = "0.8") #for annotation

            for df in dataframe_list:
                #For each dataframe (vessel queried)
                df_lenght = len(df) #getting the lenght of the  currrent dataframe

                #Extracting the values for plotting & in workable format conver to lists
                lat = df['lat'].values
                long = df['long'].values
                sog = df['sog'].values
                cog = df['cog'].values
                datetime_df = pd.to_datetime(df['datetimestamp'])

                #These paramater chages the colour of the vessel limit the amount of colours
                df_change_colour = math.floor(df_lenght/150) #there is 150 colours to choose from

                colour = 0 #incremental, denotes the startig colour
                max_sog = max(sog)  #used to scale the marker size of the plot
                offset = 60000 #Annotation offset amount

                x,y = m(lat,long) #convert long lat to basemap coordinates

                if(chk_annotation_status.get() == 1): #if annotations where selected
                    annotation_amount = annotateInterval(size = df_lenght,
                                    amount_anno =int(grid_Annotation_amt.get()))

                annotation_at_zero = 1 #set varaible to 1 if include annotation make 0
                if(chk_annotation_speed_status.get() == 1):
                    annotation_at_zero = 0 #include observations from 0


                #plotting observations of each dataframe
                for i in range(1, df_lenght):
                    sog_marker_plot = math.ceil( (sog[i]/max_sog)*3)
                    #normalizing and scaling the different speeds for different marker sizes

                    if(sog_marker_plot == 0): #if zero, scale up. cannot have 0 marker size
                        sog_marker_plot +=1

                    if(df_change_colour != 0): #Avoid devide by zero if an observation has less than  150 observations
                        if((i%df_change_colour == 0) and (colour < 149)): #149 amt of shades
                            colour += 1 #change colour shade

                    #Adding annotations
                    if(chk_annotation_status.get() == 1):
                        if((i%annotation_amount == 0) and sog[i] >= annotation_at_zero): #only annotate if speed is larger than
                            #^^^^^^^iterator % interval amnt , if == 0, good division, annotate
                            plt.annotate(
                            annotateString(sog[i],cog[i],datetime_df[i]),
                            (x[i],y[i]),
                            xytext = ((x[i]+int(0.5*offset),y[i]-offset)),
                            ha = 'center', #centre text
                            wrap = True, #wrap text
                            fontsize = 5.5,
                            arrowprops = dict(arrowstyle = "->",facecolor = 'black'), bbox = bbox) #annotation arrows

                    #Adding Arrows & stationary points
                    if(chk_annotation_arrow.get() == 1):
                        #Scaling the size
                        sog_scaled = getArrowSize(sog[i])
                        arrow_radius = (sog_scaled) #speed^4 / 2, to have an exponential scale, and divide by 2 to scale down
                        arrow_angle = (cog[i]-90)*(-1) #adjusting the scale of the basmap to compas degrees
                        #cog == course over ground in degrees, needs to be converted because basemap 0° is other way aroun(anti clock wize)

                        angle_rad = arrow_angle * math.pi/180 #conver to radiants

                        if(i%10 == 0): #plot every 10th arrow
                            arrow_head_dimentions = sog_scaled*0.7 #arrow head dimentions, also related to the speed
                            plt.arrow(x[i],y[i],
                                        (arrow_radius)*math.cos(angle_rad), #drawing the arrow (get correspondin coordinate values)
                                        (arrow_radius)*math.sin(angle_rad),
                                        head_width = arrow_head_dimentions, #width of the arrow head
                                        head_length = 100+arrow_head_dimentions, #lenght of the arrow head
                                        linewidth = 2, #arrow line width
                                        fc= (colour_palettes[col_pal])[colour], #arrow colours
                                        ec =(colour_palettes[col_pal])[colour])

                    #plot static observations
                    m.plot([x[i-1],x[i]],[y[i-1],y[i]],"o-", linewidth = 1,
                            markersize=2, c = (colour_palettes[col_pal])[colour]) #different colours

                    #Indicate stationary times
                    if (sog[i] <0.5): #0.5 speed wat which a boat is slow
                        circle = plt.Circle((x[i],y[i]),1000, color = '#9d00ff', fill = True)
                        plt.gcf().gca().add_artist(circle)
                col_pal +=1 #change colour palet
            #Draw basemap settings
            m.drawmapboundary(fill_color='#dcf6fa')
            m.drawcoastlines()
            m.fillcontinents(color = '#a8a8a8', lake_color = '#1d6bb5') #fill continents
            m.drawrivers(color = '#1d6bb5') #draw rivers

            #Adding a legend to basemap
            legend_elements =[]
            legend_elements.append(Line2D([0], [0],color='b', lw=5, label=entry_MMSI.get()))
            legend_colours = ['b','g','r']
            legend_counter  = 1  # to add appropriate colour to legend

            #if present add vessel 2
            if(chk_ship_2_status.get() == 1):
                legend_elements.append(Line2D([0], [0],color=legend_colours[legend_counter]
                                        , lw=5, label=grid_Ship_2.get()))
                legend_counter += 1 #add if 3 is also chosen
            #if present add vessel 3
            if(chk_ship_3_status.get() == 1):
                legend_elements.append(Line2D([0], [0],color=legend_colours[legend_counter],
                                        lw=5, label=grid_Ship_3.get()))


            #Adding long and lat lines intervals to the maps
            parallels = np.arange(0.,60.,2.) #increments of the longitude
            m.drawparallels(parallels,labels=[False,True,True,False], fontsize = 14)
            meridians = np.arange(-10.,40.,2.)
            m.drawmeridians(meridians,labels=[True,False,False,True], fontsize = 14)

            plt.legend(handles = legend_elements, loc = 'best', fontsize = 14,
                        title = "MMSI's",title_fontsize = 14) #add legend at best location
            plt.tight_layout(pad = 4) #stretch plot
            plt.xlabel("Longitude", fontsize = 15, labelpad = 25)
            plt.ylabel("Latitude", fontsize = 15, labelpad = 30)
            plt.title("Static plot of vessels", pad = 5, size = 18)
            plt.get_current_fig_manager().full_screen_toggle()
            plt.show() #start plot

        def annotationObjectState(status):
            """
            This function will toggle the state of the annotation related objects

            Parameters
            ----------
            status: int
                Indicate the status of a tKinter object
                1 = active,
                0 = disable

            """
            if(status == 1): #enable
                grid_Annotation_amt['state'] = "enable"
                chk_annotation_speed['state'] = 'active'
                grid_Annotation_amt.current(11)
            else: #disable
                grid_Annotation_amt['state'] = "disabled"
                chk_annotation_speed['state']  =  'disabled'

        def objectStatiMMSIState(objState):
            """
            This function will change all the object states listed

            Parameters
            ----------
            objState: string
                String will be sent to switch the state
            """
            grid_Ship_2["state"] = objState
            grid_Ship_3["state"] = objState
            btn_staticPlot["state"] = objState
            grid_quality["state"] = objState

            if(objState == 'enable'):
                chk_ship2["state"] = "active"
                chk_ship3["state"] = "active"
                chk_annotation["state"] = "active"
                chk_arrows["state"] = "active"
            else:
                chk_ship2["state"] = "disabled"
                chk_ship3["state"] = "disabled"
                chk_annotation["state"] = "disabled"
                chk_annotation_speed['state'] = 'disabled'
                chk_arrows["state"] = 'disabled'

            #MMSI entered dataframe
            mmsi_main_df = []

        def searchMMSI_static():
            """
            This function does error handeling and catching, makes sure
            that a specific mmsi exists and that the user may continue or not

            """
            all_tests_passed = False
            #Testing if the MMSI exists
            try:
                db_query = ("SELECT mmsi FROM " + str(database_table) +
                 " WHERE mmsi = " +str(entry_MMSI.get()) + " LIMIT 1;")
                temp = readDatabase(db_query) #get information from the Database
                if(len(temp) == 0): # tests wheter there is data present
                    btn_staticPlot['state'] = 'disabled' #user cannot proceed or plot
                    objectStatiMMSIState("disable") #making sure user cannot contiue
                    popMsg("MMSI does not exist / Zero Observations") #Error
                else:
                    all_tests_passed = True #if no errors
                    objectStatiMMSIState('enable')

            except Exception as err  :
                objectStatiMMSIState("disable") #making sure user cannot contiue
                print(err)
                popMsg("Please enter a valid MMSI") #error to user

            if(all_tests_passed == True): #if no errors
                addGridData()

        def addGridData():
            """
            If all error handling was passed this function will be envoked
            The grid options will be filled by the nearest 20 mmsi' values of the
            selected mmsi

            The main MMSI values will be setted here so that we dont query the
            database unnessesarely
            """
            #Set values and query the database
            mmsi_main_df = readDatabase(
            str("SELECT mmsi, ST_X(geom::geometry) as lat, ST_Y(geom::geometry) as long, " +
            " sog, datetimestamp FROM " + database_table+" WHERE (MMSI = "+ str(entry_MMSI.get()) +
            ")  ORDER BY datetimestamp ASC"))

            #Get the average LOGITUDE and latitude value so that we can get vessels in the area
            lat_mean =  np.mean(mmsi_main_df["lat"].values)
            long_mean =  np.mean(mmsi_main_df["long"].values)

            #The query for retrieving the nearest mmsi's of the inputed mmsi
            query_near_20 = str("SELECT mmsi FROM " + str(database_table)+
            " WHERE (sog > 0) and  (sog < 30) and ST_DWithin(geom::geography," +
            "ST_GeogFromText('POINT(" +str(lat_mean) +" " + str(long_mean) + ")'),(1000)*1000, false) LIMIT 20;")
            #radius of 1000km

            #getting the date
            df_mmsi = readDatabase(query_near_20)
            #setting the mmsi values to the grids objects
            grid_Ship_2["values"] =  ((df_mmsi["mmsi"].values).astype(int)).tolist()#convert to list
            grid_Ship_2.current(1)
            grid_Ship_3["values"] =  ((df_mmsi["mmsi"].values).astype(int)).tolist() #convert to list
            grid_Ship_3.current(10)

####---------------------------END OF STATIC MAP FRAME -------------------------


####--------------------- CLASS: HEATMAP FRAME ---------------------------------
#Declaring a global variable, label so that there can be an update in the message
lbl_Patient = 0
class HeatMapFrame(tk.Frame):
    """
    This class is the Spatial Distribution Map frame and the options the user have.

    Gridboxes = select the quality of the plot and radius of observations to plot
    within the selected point

    Buttons = to go back or to start plot
    """

    def __init__(self,parent,controller):
        #Frame settings
        tk.Frame.__init__(self,parent)
        self.configure(background = BACKGROUND_COLOUR) #Setting the background colour
        global lbl_Patient

        #Defining labels for the frame
        lbl_heatmap_heading = ttk.Label(self,text = "Spatial Distribution Map",
                            font = HEADING_FONT, background = BACKGROUND_COLOUR)
        lbl_chooseRadius = ttk.Label(self,text = "Radius size:",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)
        lbl_dummySpace = ttk.Label(self,text ="       ",
                            font =("Century Gothic",20),background = BACKGROUND_COLOUR)

        lbl_SOG_UpLow = ttk.Label(self,text = "SOG:",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)

        lbl_sogLower = ttk.Label(self,text = "lower bound",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)
        lbl_sogUpper = ttk.Label(self,text = "upper bound",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)
        lbl_Quality =  ttk.Label(self,text ="Quality of plot:",
                            font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        #The following dummy label is to adjust for the size of the border
        lbl_dummy = ttk.Label(self,text ="       ",
                            font =("Century Gothic",50),background = BACKGROUND_COLOUR)
        lbl_dummy_2= ttk.Label(self,text =" ",
                            font =("Century Gothic",20),background = BACKGROUND_COLOUR)
        lbl_chooseRadiusKM = ttk.Label(self,text = "km",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)
        #notifying the user that the bounds are inclusive
        lbl_boundsInclusive = ttk.Label(self,text = "*bounds are inclusive",
                            font = ("Century Gothic",8), background = BACKGROUND_COLOUR)
        lbl_Patient = ttk.Label(self,text = "",
                            font = ENTRY_FONT, background = BACKGROUND_COLOUR)

        #Defining the Combobox objects
        #The radius is denoted in kilometers from the selected dot
        grid_Radius= ttk.Combobox(self, font = ENTRY_FONT)
        grid_Radius['values']= (np.arange(100,510,10)).tolist()
        grid_Radius.current(8) #Setting the default, starting value

        #Combobox for the sog bounds for the heatmaps
        grid_lowerBound= ttk.Combobox(self, font = ENTRY_FONT)
        grid_lowerBound['values']= (np.arange(0,150,1)).tolist()
        grid_lowerBound.current(0) #Setting the default, starting value

        grid_UppperBound= ttk.Combobox(self, font = ENTRY_FONT)
        grid_UppperBound['values']= (np.arange(0,150,1)).tolist()
        grid_UppperBound.current(100) #Setting the default, starting value

        #Quality of the plot combo option
        grid_quality = ttk.Combobox(self, font = ENTRY_FONT)
        grid_quality['values']= ('Low','Intermediate','High','Full (takes time)')
        grid_quality.current(1) #default intermediate

        #initiate the choosing ability to select the centre of the radius that will be plotted
        btn_chooseCentre = ttk.Button(self,text="Choose Centre", width = 15,
                            style = 'NAV.TButton', command = lambda: chooseCentre())
                            #lambda delays the function that it ist not executed on startup

        btn_back= ttk.Button(self,text="Back", width = 15, style = 'NAV.TButton',
        command = lambda: controller.show_frame(WelcomeScreen) ) #command = funtion to execute

        #configuration of the tkinter objects and placements
        lbl_heatmap_heading.config(anchor = CENTER) #centre the tex
        lbl_heatmap_heading.grid(row=0, column = 1, columnspan = 3,padx = 20,
                            pady = BUTTON_PADY)
        lbl_dummy.grid(row = 1, column = 0,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_dummy_2.grid(row = 1, column = 0,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_chooseRadius.grid(row =2, column = 1, sticky = 'e',padx = BUTTON_PADX,
                            pady = BUTTON_PADY)
        grid_Radius.grid(row = 2, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_Quality.grid(row = 3, column = 1, sticky = 'e',padx = BUTTON_PADX,
                        pady = BUTTON_PADY)
        grid_quality.grid(row= 3, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)

        lbl_chooseRadiusKM.config(anchor = 'e')
        lbl_chooseRadiusKM.grid(row = 2, column = 3, sticky = 'w',padx = BUTTON_PADX,
                            pady = BUTTON_PADY)

        lbl_dummySpace.grid(row= 4, column = 0,padx = BUTTON_PADX, pady = BUTTON_PADY)

        lbl_SOG_UpLow.grid(row= 5, column = 0,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_sogLower.grid(row= 5, column = 1,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_sogUpper.grid(row= 5, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)
        grid_lowerBound.grid(row= 6, column = 1,padx = BUTTON_PADX, pady = BUTTON_PADY)
        grid_UppperBound.grid(row= 6, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_boundsInclusive.grid(row= 6, column = 3,padx = BUTTON_PADX, pady = BUTTON_PADY)

        btn_chooseCentre.grid(row=10,column = 3, pady = 10)
        btn_back.grid(row=11, column = 3,padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_Patient.grid(row=12,column = 3, pady=50, columnspan = 10)


        def chooseCentre():
            """
            This function creates a basemap plot that will be showed, the user
            can then select a spot on the map and a radius of the selected amount
            of kilometers will be drawn around the selected point.

            The user must double-click:
                The first click allows for the drawing of "Centre of radius"
                and the second click initiates the basemap heatmap plot
            """

            plt.close() #close any open plots
            #sets the label text
            lbl_Patient.configure(text = "Please be patient the heatmap takes time")
            #the figure size of the area to be selected
            plt.figure(figsize=(10,7))
            m = Basemap(projection = 'mill',
            llcrnrlat =30, #30
            llcrnrlon=-12, #-12
            urcrnrlat =52, #52
            urcrnrlon =35, #35
            resolution = 'i')

            m.drawmapboundary(fill_color='#dcf6fa')
            m.drawcoastlines()
            m.fillcontinents(color = '#a8a8a8', lake_color = '#1d6bb5') #fill continents
            m.drawrivers(color = '#1d6bb5') #draw rivers

            #longitude and latitude on map
            parallels = np.arange(0.,60.,5.) #increments of the longitude
            m.drawparallels(parallels,labels=[False,True,True,False], fontsize = 14) #drawing
            meridians = np.arange(-10.,40.,5.)
            m.drawmeridians(meridians,labels=[True,False,False,True], fontsize = 14)

            lon, lat = -104.237, 40.125 # inital values
            xpt,ypt = m(lon,lat)# convert to map projection coords.
            # convert back to lat/lon
            lonpt, latpt = m(xpt,ypt,inverse=True) #get the inverse, from plot to long lat
            point, = m.plot(xpt,ypt,'bo')  # plot a blue dot there
            # put some text next to the dot, offset a little bit
            # creating the annotation
            annotation = plt.annotate(' (%5.1fW,%3.1fN)' % (lon, lat),
                            xy=(xpt,ypt),xytext=(20,35), textcoords="offset points",
                            bbox={"facecolor":"w", "alpha":0.5},
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3"))

            def onclick(event):
                """
                This fontion takes in event that contains data from where the
                user clicked on the basemap plot

                The annotation is drawn and then the query is sent to the drawHeatmapnow
                function that will start the heatmap plot
                """
                global click_times # global varaible to count amount of times clicked
                ix, iy = event.xdata, event.ydata # getting the x y from the click
                xpti, ypti = m(ix, iy,inverse=True) # coordiantes from the point selected
                annotation.xy = (ix, iy) # making a label
                point.set_data([ix], [iy])
                annotation.set_text("Centre of radius") # text to display
                annotation.set_fontsize(15)
                plt.gcf().canvas.draw_idle() # draw label

                if(click_times == 1):
                    lowerSOG = grid_lowerBound.get()
                    upperSOG = grid_UppperBound.get()
                    drawHeatmapnow(xpti,ypti,grid_Radius.get(),lowerSOG,upperSOG,str(grid_quality.get()[0]).lower())
                    """
                    x & y coordinate of clicked location i sent to the functions
                    as well as the radius size and the quality of the plot
                    grid_Radius.get() get the km
                    """
                    ini_test = 0 #set back to 0
                click_times = click_times+1 #increment after click 1

            #for on click functionality on matplotlib
            cid = plt.gcf().canvas.mpl_connect("button_press_event", onclick)
            plt.tight_layout() #make a tight layout fill the white space
            #Adding labels describing the plot
            plt.xlabel("Longitude", labelpad = 25, size = 15)
            plt.ylabel("Latitude", labelpad = 20, size = 15)
            #Adding the heading
            plt.title("Choose the centre of the radius by double clicking", size = 18, pad = 10)
            plt.show() #show plot

####-------------------- END OF HEATMAP FRAME CLASS ----------------------------


click_times = 0 #Global variable to record number of clicks
def drawHeatmapnow(xpti,ypti,radius_size,lowSOG,UpSOG,plt_quality):

    """
    This function creates a database query and receives a dataframe,
    the information is then extracted into arrays and sent to basemap coordiante
    converter and plotted as a heatmap with the hexbin function

    PARAMETERS
    ----------
    xpti: float
        The x coordinate of the selected spot on the map
    ypti: float
        The y coordiante of the selected spot on the map
    radius_size : int
        The size of the radius in kilimoters around the selected spot that
        the heatmap should consist out of
    lowSOG : float
        This is the lower bound of the speed that should be plotted
    UpSOG : float
        This is the upper bound of the speed that should be plotted
    plt_quality : str
        Basemap quality of the plot

    SQL Query Deconstriction (written in PostgreSQL)
    -------------------------

    ST_DWithin: PostGIS FUCNTION
        Return all the points within spacified range in kilimeters

    SQL QUERY:
        SELECT ST_X(geom::geometry) as lat, ST_Y(geom::geometry) as long
        FROM [Database table name]
        WHERE
            sog > 0  --speed larger than 0
            AND
            ST_DWithin(geom::geography,
                        ST_GeogFromText('POINT([selected x] [selected y])) +")'),
                        [radius size]*1000, false);" -- points within radius
        ST_DWithin: PostGIS FUCNTION
            Return all the points within spacified range in meters
            the value [radius size is scaled to meters with *1000]
            as that is the input value of ST_DWithin

    """
    global click_times
    click_times = 0 #reset value

    # SQL Query
    queryHeat = str( "SELECT ST_X(geom::geometry) as lat, ST_Y(geom::geometry) as long FROM " +
        database_table + " WHERE ST_DWithin(geom::geography,ST_GeogFromText('POINT("+
        str(round(xpti,2)) +" "+str(round(ypti,2)) +")'),"+str(float(radius_size)*1000)+", false) and (sog >=" +
        str(lowSOG)  +") and (sog <= " + str(UpSOG) +")")


    #Exception handling when querying the database
    try:
        df_in = readDatabase(queryHeat)
    except Exception as err :
        print("Error read database, Heatmap\n", err)

    # Extracting the values from dataframe to an array
    # .values ~extracts as an array
    arr_Long = df_in['long'].values
    arr_Lat= df_in['lat'].values
    # Get the min and max values for the basemap region size
    long_min = min(arr_Long)
    long_max = max(arr_Long)
    lat_min = min(arr_Lat)
    lat_max = max(arr_Lat)

    plt.close() # close any open plots

    plt.figure(figsize=(10,10)) # figure size of basemap
    m = Basemap(projection = 'mill',
    llcrnrlon = lat_min, # flipping the observations for correct dimentions
    urcrnrlon = lat_max,
    urcrnrlat = long_max,
    llcrnrlat = long_min,
    resolution = plt_quality) #h= high f= full i= intermediate

    xpt, ypt = m(arr_Lat,arr_Long)  #convert inputs to basemap and convert from a dataframe to array
    # Creating the heatmap plot
    heatmap = m.hexbin(xpt,ypt,bins = 'log',gridsize = 1000, cmap=plt.cm.viridis) #cmap=plt.cm.viridis

    cbar = m.colorbar(heatmap, location='right',shrink = 0.6)
    cbar.ax.tick_params(labelsize = 25)
    #cbar.set_label(, size = 14)
    cbar.ax.set_ylabel('Number of observations per colour',rotation = 270,size = 15, labelpad = 30)
    m.drawmapboundary(fill_color='#dcf6fa')
    m.drawcoastlines()
    m.fillcontinents(color = '#a8a8a8', lake_color = '#1d6bb5') #fill continents
    m.drawrivers(color = '#1d6bb5') #draw rivers and set their colours
    plt.title("Spatial Distribution Map", size = 18)
    plt.tight_layout(pad = 5) # fill the white space
    plt.get_current_fig_manager().full_screen_toggle() #make FULL SCREEN
    plt.show() #show the plot

#####------------------ END OF HEATMAP PLOT FUNCTION ---------------------------


####----------------Database Login Page FRAME-----------------------------------
class DBLoginPage(tk.Frame):
    """
    This class is for the database login for the user.
    """
    def __init__(self,parent,controller):
        #Frame settings
        tk.Frame.__init__(self,parent)
        self.configure(background = BACKGROUND_COLOUR)

        # Declaring figures and their locations, a visual database connection indicator
        img_red = ImageTk.PhotoImage(Image.open(IMAGE_DIRECTORY +
                                    str('Red_status_Large.png')).resize((340,170)))
        img_green = ImageTk.PhotoImage(Image.open(IMAGE_DIRECTORY +
                                    str('Green_status_Large.png')).resize((340,170)))
        img_orange = ImageTk.PhotoImage(Image.open(IMAGE_DIRECTORY +
                                    str('Orange_status_Large.png')).resize((340,170)))
        # adding the image to the label
        lbl_ship = ttk.Label(self,image= img_orange)
        lbl_ship.image = img_orange # default status = orange, database untested

        #Defining labels
        lbl_DatabaseLogin = ttk.Label(self,text ="Database Login", font =HEADING_FONT) #defined a label
        label_Username = ttk.Label(self,text ="Username:", font =LABEL_FONT)
        label_Password= ttk.Label(self,text ="Password:", font =LABEL_FONT)
        label_ip = ttk.Label(self,text ="IP address:", font =LABEL_FONT)
        label_DBName = ttk.Label(self,text ="DB Name:", font =LABEL_FONT)
        label_TableName = ttk.Label(self,text ="Table Name:", font =LABEL_FONT)
        label_conn_status = ttk.Label(self,text ="Connection status: Untested", font =LABEL_FONT)

        #Adding label configurations:
        my_label_list = [lbl_DatabaseLogin,label_Username,label_Password,label_ip,label_DBName,label_TableName] #list of all the labels
        for lbl in my_label_list:
            lbl.configure(background = BACKGROUND_COLOUR)
        lbl_ship.configure(background = BACKGROUND_COLOUR)
        label_conn_status.configure(background = BACKGROUND_COLOUR)

        #Creating entry box objects
        entry_UserName = ttk.Entry(self,font =ENTRY_FONT)
        entry_Password = ttk.Entry(self,show = "*", font =ENTRY_FONT)
        entry_ip = ttk.Entry(self,font =ENTRY_FONT)
        entry_DBName = ttk.Entry(self,font =ENTRY_FONT)
        entry_TableName = ttk.Entry(self,font =ENTRY_FONT)

        #Creating entrybox list for easy defining
        entrybox_list = [entry_UserName,entry_Password,entry_ip,entry_DBName,entry_TableName]

        #Adding information to the text boxes - for faster testing
        entry_UserName.insert(0 ,'postgres')
        entry_Password.insert(0, '!')
        entry_ip.insert(0, '127.0.0.1')
        entry_DBName.insert(0 ,'NARI_MBDW' )
        entry_TableName.insert(0 , '')


        def test_DB():
            """
            This function is for checking the datbase and if all information
            entered is valid and that it is possible to connect to the database
            for all future transactions within the application with the database

            """
            all_tests_passed = True # to check if tessts passed, inital variable

            #Setting variables
            username= str(entry_UserName.get())
            password =str(entry_Password.get())
            ip = str(entry_ip.get())
            name = str(entry_DBName.get())
            tblname = str(entry_TableName.get())

            def errorinDB():
                """
                This function is for when the user enter incorrect information
                so that the image will change from orange/green to red
                """
                lbl_ship = ttk.Label(self,image= img_red)
                lbl_ship.image = img_red # load red image
                lbl_ship.configure(background = BACKGROUND_COLOUR)
                # place the label
                lbl_ship.grid(column = 0, row = 1, rowspan = 7,
                            padx = BUTTON_PADX, pady = 30)
                # update connections status
                label_conn_status.configure(text = "Connection status: Bad") #Notify status
                # keep proceed button disapled
                btn_proceed["state"] = "disabled" # keep button disabled

            try: # try credentails entered
                #create database connection
                database_connection = sqlalchemy.create_engine(
                'postgres+psycopg2://{0}:{1}@{2}/{3}'.format(username, password,
                ip, name), pool_recycle=1, pool_timeout=57600).connect()

            except:
                errorinDB() #Calling error
                popMsg("Database Credential Error") #error in credentails

            try: #try a query to validate it
                #Small(fast) database query to test the table existance
                test_Query = ("SELECT mmsi FROM " +str(tblname) + " LIMIT 1;")
                temp = pd.read_sql_query(test_Query, database_connection) #read database
                database_connection.close() #close connection
            except:
                errorinDB()
                popMsg("Table Credential Error")

            #If statement for options to do if all databse requirements is passed
            if(all_tests_passed == True):
                #Change animation to green
                lbl_ship = ttk.Label(self,image= img_green) #Ship label
                lbl_ship.image = img_green #change ship icon
                lbl_ship.configure(background = BACKGROUND_COLOUR)
                # place the label
                lbl_ship.grid(column = 0, row = 1, rowspan = 7,
                        padx = BUTTON_PADX, pady = 30)
                # update label status
                label_conn_status.configure(text = "Connection status: Good")
                # update button state, allow user to proceed
                btn_proceed["state"] = "enabled"

                #Global variables so that they are availible everywhere in the application
                global database_username, database_password, database_ip, database_name
                global database_table

                # Getting text inputs form text boxes
                database_username = str(entry_UserName.get())
                database_password = str(entry_Password.get())
                database_ip = str(entry_ip.get())
                database_name = str(entry_DBName.get())
                database_table = str(entry_TableName.get())
            else:
                # Connection failed - indicate a red animation
                errorinDB()

        # Create a button style
        btn_NAV_STYLE = ttk.Style()
        btn_NAV_STYLE.configure('NAV.TButton', font = ("Century Gothic",11))

        # Creating button objects:
        btn_dbtest = ttk.Button(self,text="Test Database", width = 25,
                                style = 'NAV.TButton',command = lambda:  test_DB())

        # proceed button decleration
        btn_proceed = ttk.Button(self,text="Proceed", width = 25, style = 'NAV.TButton',
                                command = lambda:  controller.show_frame(WelcomeScreen))
        btn_proceed["state"] = "disabled" #keep button disabled until DB connection is passed

        #LABEL Placement:
        lbl_ship.grid(column = 0, row = 1, rowspan = 7, padx = BUTTON_PADX, pady = 30)

        # Adding label info
        lbl_row = 2  # to iterate over the list and set row numers
        for lbl in my_label_list: # for each label in the list
            lbl.grid(row= lbl_row, column =1,sticky = 'e', padx = BUTTON_PADX, pady = BUTTON_PADY)
            lbl_row = lbl_row+1

        # place the connection status row
        lbl_DatabaseLogin.grid(row = 0, column = 0,columnspan = 4,sticky = 'n',
                                padx = BUTTON_PADX, pady = 30)
        label_conn_status.grid(row = 8, column = 0)

        #Entry box Allignment:
        txt_row  =3
        for txt_box in entrybox_list:
            txt_box.grid(row =txt_row ,column = 2, padx = BUTTON_PADX, pady = BUTTON_PADY)
            txt_row =txt_row +1

        #Button Allignment:
        btn_dbtest.grid(row = 8, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)
        btn_proceed.grid(row = 9, column = 2,padx = BUTTON_PADX, pady = BUTTON_PADY)

#####---------------------- END OF Database LOGIN window------------------------

#Global varaibles for fonts
ANS_FONT_STATS = ("Century Gothic",14)
HEADING_FONT_STATS = ("Century Gothic",30, 'underline bold')
PROJ_NAME_FONT = ("Century Gothic",55, 'underline bold')
HEADING_2nd_FONT_STATS =  ("Century Gothic",20,"underline bold")

####---------------------- VESSEL STATISTICS FRAME -----------------------------
class VesselStats(tk.Frame):
    """
    This class is for the form that display the vessel statistics, all the statistical
    information relatied to the queried vessel MMSI.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        #Setting background of current frame
        self.configure(background = BACKGROUND_COLOUR)

        #Creating label objects
        lbl_stats_heading = ttk.Label(self,text ="Vessel Statistics",
                            font =HEADING_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_MMSI =  ttk.Label(self,text ="Enter Vessel MMSI:",
                            font =LABEL_FONT,background = BACKGROUND_COLOUR)

        lbl_dummy = ttk.Label(self,text ="             ",font =("Century Gothic",20),
                                    background = BACKGROUND_COLOUR)
        lbl_VesselStats = ttk.Label(self,text ="Statistics", font =HEADING_2nd_FONT_STATS,
                                    background = BACKGROUND_COLOUR)
        lbl_vesselLongRange = ttk.Label(self,text ="Longitude Range:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_vesselLatRange = ttk.Label(self,text ="Latitude Range:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_maxSpeed = ttk.Label(self,text ="Max Speed:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_vesselAVG_SOG = ttk.Label(self,text ="Average SOG:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_vesselAVG_SOG_LargerZero =ttk.Label(self,text ="Average SOG >0:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_vessel_observations = ttk.Label(self,text ="Total Observations:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)
        lbl_vessel_stationary = ttk.Label(self,text ="Stationary Observations:",
                                        font =ANS_FONT_STATS,background = BACKGROUND_COLOUR)


        ans_lbl_VesselStats = ttk.Label(self,text =" ", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vesselLongRange = ttk.Label(self,text ="[,]", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vesselLatRange = ttk.Label(self,text ="[,]", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_maxSpeed = ttk.Label(self,text ="- kt", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vesselAVG_SOG = ttk.Label(self,text ="- kt", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vesselAVG_SOG_LargerZero =ttk.Label(self,text ="- kt", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vessel_observations = ttk.Label(self,text ="-", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)
        ans_lbl_vessel_stationary = ttk.Label(self,text ="-", font =ANS_FONT_STATS,
                                background = BACKGROUND_COLOUR)

        #Creating a list of all the lables to reduce repetative coding
        lbl_vesselStats_list = [lbl_MMSI, lbl_dummy,
                                lbl_VesselStats,lbl_vesselLongRange,
                                lbl_vesselLatRange,lbl_maxSpeed,
                                lbl_vesselAVG_SOG,lbl_vesselAVG_SOG_LargerZero,
                                lbl_vessel_observations,lbl_vessel_stationary]
        #Creating a list of all the lables to reduce repetative coding
        ans_vesslStats_list = [ans_lbl_VesselStats,ans_lbl_vesselLongRange,
                                ans_lbl_vesselLatRange,ans_lbl_maxSpeed,
                                ans_lbl_vesselAVG_SOG,ans_lbl_vesselAVG_SOG_LargerZero,
                                ans_lbl_vessel_observations,
                                ans_lbl_vessel_stationary]

        #Entry boxe object for the vessel id
        entry_MMSI = ttk.Entry(self,font =ENTRY_FONT)
        entry_MMSI.insert(0,'227003050') #default vessel id
        #667001286
        #240985000

        #Functions
        def MMSIExists():
            """
            This function is for testing whether a MMSI exists and querying
            the databse if it does and filling in the statistics in the appropriate
            label
            """

            global mmsi_entry #set the global variable to the entered mmsi
            mmsi_entry = entry_MMSI.get()  #get the mmsi from the textbox
            try: #try connection, test if mmsi exists
                db_query = ("SELECT mmsi FROM " + str(database_table) +
                 " WHERE mmsi = " +str(mmsi_entry) + " LIMIT 1;")

                temp = readDatabase(db_query) #get information from the Database
                if(len(temp) == 0): # tests weather there is data present
                    btn_plot_tool['state'] = 'disabled' #user cannot proceed
                    popMsg("MMSI does not exist / Zero Observations") #Error

                else:
                    # if there is an observation do the following
                    try:
                        getStats(mmsi_entry) #set and get all the statistics
                        setStatLabels() #Setting the labels to their values
                        plt.show()
                    except Exception  as err:
                        btn_plot_tool['state'] = 'disabled' #keep plotting button disabled
                        popMsg(str("Error in StatsQuery: " +err))
            except: #The MMSI is not valid at all
                btn_plot_tool['state'] = 'disabled' #keep plotting button disabled
                popMsg("Invalid MMSI") #Show error


        def getStats(mmsi_entry):
            # Declaring global variable to set their values
            global vesselName,vesselDim,vesselType
            global vesselLong_min,vesselLong_max,vesselLat_max,vesselLat_min
            global vesselMaxSpeed,vesselAVG_SOG ,vesselAVG_SOG_LargerZero
            global vessel_observations,vessel_stationary
            #Global DATAFRAMES TO BE SET
            global df_Longitude,df_Latitude,df_SOG ,df_NAV_status , df_vessel_time,df_COG
            #Global variables for future functionality
            VesselName = 'NA'
            VesselDim = 'NA'
            VesselType = 'NA'

            #Database query, ST_X = convert to lat, ST_Y = convert to long
            myQuery = str("SELECT mmsi, ST_X(geom::geometry) as latitude, ST_Y(geom::geometry) as longitude, sog, cog, navstat, datetimestamp FROM "+
            str(database_table)+ " WHERE mmsi = "+ str(mmsi_entry) + " ORDER BY datetimestamp ASC")

            # Exception handling try to read the database, there should'nt be an error
            try:
                queryData = readDatabase(myQuery) #save dataframe as queryData
            except:
                popMsg("Database read FAILED")

            # Assigning the global dataframes to variables from the database query
            df_Longitude = queryData.loc[:,'longitude']
            df_Latitude = queryData.loc[:,'latitude']
            df_SOG = queryData.loc[:,'sog']
            df_NAV_status = queryData.loc[:,'navstat']
            df_vessel_time = queryData.loc[:,'datetimestamp']


            df_COG = queryData.loc[:,'cog'] #extracting the course over ground

            #Extracting statistics and saving them
            vesselLong_min = min(df_Longitude)
            vesselLong_max = max(df_Longitude)
            vesselLat_max = max(df_Latitude)
            vesselLat_min = min(df_Latitude)
            vesselMaxSpeed = max(df_SOG)
            vesselAVG_SOG = round(np.mean(df_SOG),4) #round to the nearest 4 characters
            vesselAVG_SOG_LargerZero = round(np.mean(df_SOG[df_SOG>0]),4) #all the observations where the speed is larger than 0
            vessel_observations = len(df_Longitude) #all the observations
            vessel_stationary = len(df_SOG[df_SOG == 0]) #stationary observations

            #Adding a matplotlib statistics graph
            data_lenght = len(df_SOG)
            x_points = np.arange(0,data_lenght) #listing number of observations
            plt.plot(x_points,np.array(df_SOG),label = "Speed")
            plt.plot(x_points,np.repeat(vesselMaxSpeed,data_lenght), color = 'r', label = 'Max Speed')
            plt.plot(x_points,np.repeat(vesselAVG_SOG,data_lenght), color = 'g', label = 'Average Speed')
            plt.plot([0,data_lenght],[vesselAVG_SOG_LargerZero,vesselAVG_SOG_LargerZero], label = "Avg speed sog > 0")
            plt.xlim(right=(data_lenght + 250)) #setting the limit on the x-axis

            xticks_np = np.arange(0,data_lenght, math.ceil(data_lenght**0.5)) #removing ticks
            plt.xticks(xticks_np," ")
            plt.xlabel("Observations", fontsize = 14)
            plt.ylabel("Speed in knots", fontsize = 14)
            plt.title(str("Plot for MMSI ID: " + str(mmsi_entry)), size = 14)
            plt.legend(loc ="best",prop={'size': 11}) #setting legend to the best location and its text size

            #-------------------END OF GET STATS FUCNTION--------------------

#Function - set labels:
        def setStatLabels():
            """
            This function sets all the labels in the statistics form to the
            statistics extracted from the database
            """
            btn_plot_tool['state'] = 'enabled' #enabling plotting button
            lbl_plot_heading.configure(text= str("Animation Settings for MMSI: " +
                                        str(mmsi_entry)))

            #Setting all label
            ans_lbl_vesselLongRange.configure(text = str("["+str(vesselLong_min) +
                                    " , " + str(vesselLong_max)+"]"))
            ans_lbl_vesselLatRange.configure(text = str("["+str(vesselLat_min) +
                                    " , " + str(vesselLat_max)+ "]"))
            ans_lbl_maxSpeed.configure(text = str(str(vesselMaxSpeed) + ' knots'))
            ans_lbl_vesselAVG_SOG.configure(text =str(str(vesselAVG_SOG) +' knots'))
            ans_lbl_vesselAVG_SOG_LargerZero.configure(text =str(str(vesselAVG_SOG_LargerZero)+
                                                        ' knots'))
            ans_lbl_vessel_observations.configure(text =str(vessel_observations))
            ans_lbl_vessel_stationary.configure(text =str(vessel_stationary))

            #---END OF SET LABELS FUNCTION

        #defining a button style
        btn_NAV_STYLE = ttk.Style()
        btn_NAV_STYLE.configure('NAV.TButton', font = ("Century Gothic",11))

        #Defining the buttons
        btn_getStats = ttk.Button(self,text="Search", width = 20, style = "NAV.TButton",
        command = lambda:  MMSIExists()) #check if mmsi exists

        btn_plot_tool = ttk.Button(self,text="Create Animation",width = 20,style = "NAV.TButton",
        command = lambda: controller.show_frame(PlotFrame)) #show plotting frame
        btn_plot_tool["state"] = "disabled"

        btn_back = ttk.Button(self,text="Back",width = 20,style = "NAV.TButton",
        command = lambda: controller.show_frame(WelcomeScreen)) #show welcome frame


        #Setting objects allignment
        entry_MMSI.grid(row= 1, column =2) # entry box
        #buttons
        btn_getStats.grid(row=1, column = 3, padx =10, pady =BUTTON_PADY)
        btn_plot_tool.grid(row=18, column = 3, padx =10, pady =BUTTON_PADY)
        btn_back.grid(row =19, column = 3, padx =10, pady =BUTTON_PADY)

        lbl_row = 1 #start at row 1
        for lbl in lbl_vesselStats_list:
            lbl.grid(row = lbl_row, column = 1, padx = BUTTON_PADX, pady=2,sticky ='w')
            lbl_row = lbl_row +1

        lbl_row = 3 #start at row 2
        for lbl in ans_vesslStats_list:
            lbl.grid(row = lbl_row, column = 2, padx = BUTTON_PADX, pady=2,sticky ='w')
            lbl_row = lbl_row +1

        #Heading allignment
        lbl_stats_heading.grid(row = 0, column = 0, columnspan =5,padx = BUTTON_PADX, pady = BUTTON_PADY)


####--------------------- END OF VESSEL STATISTICS FRAME -----------------------

#Creating a global variable to change the text of the Plotting Seettings for MMSI: [MMSI ID]
lbl_plot_heading = 0
lbl_progress = 0

#CONSTANT FONTS TO BE USED
PLOT_FONT_Heading = ("Century Gothic",16, "underline")
PLOT_FONT_Label = ("Century Gothic",14)

#Colour palette options for ship clours
PLOT_PALLET = ("Red","Green","Blue")

#Global Variable for plotting colour pallet to be saved
COLOUR_PALLET = []

# PLOTTING PARAMETERS GLOBAL VARIABLES
OBSERVATION_SKIP = 1 # amont of observations o skip in the animation funcition
PLOTTING_INTERVAL = 0.4 # intervals to plot

# Point to be used to start the plotting of lines between to coordiantes
point = 0

# basemap global varable
m = 0
####-------------------------- ANIMATION FRAME/WINDOW --------------------------
class PlotFrame(tk.Frame):
    """
    This class is for the plotting function of the animation of a vessel, as
    certian mmsi. The user can choose ploting quality, speed and all related
    information
    """

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent) #running intial
        #Setting background of current frame
        self.configure(background = BACKGROUND_COLOUR)
        #Global variables so that the value is changed globally

        global lbl_plot_heading, lbl_progress

        # Defining labels
        lbl_plot_heading = ttk.Label(self,text =str("Plot settings for MMSI: " +
                                    str(mmsi_entry)),
                                    font =("Century Gothic",25,"underline bold"),
                                    background = BACKGROUND_COLOUR)

        lbl_progress= ttk.Label(self,text ="Progress: 0%", font =PLOT_FONT_Label,
                            background = BACKGROUND_COLOUR)
        # Defining label objects
        lbl_Quality =  ttk.Label(self,text ="Quality of plot:",
                                font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        lbl_dummy = ttk.Label(self,text ="             ",
                    font =("Century Gothic",20),background = BACKGROUND_COLOUR)
        lbl_dummy_2 = ttk.Label(self,text ="             ",
                    font =("Century Gothic",24),background = BACKGROUND_COLOUR)
        lbl_obs_skip = ttk.Label(self,text ="Each i'th observation to plot:",
                                font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        lbl_plot_speed = ttk.Label(self,text ="Plotting speed (seconds):",
                                font =PLOT_FONT_Label,background = BACKGROUND_COLOUR)
        lbl_ColourPalette = ttk.Label(self,text ="Colour:",
                                font=PLOT_FONT_Label ,background = BACKGROUND_COLOUR)

        # Defining comboboxes
        grid_quality = ttk.Combobox(self, font = ENTRY_FONT)
        grid_quality['values']= ('Low','Intermediate','High', 'Full (takes time)') #settings
        grid_quality.current(1) # default

        #observations to skip
        grid_obs_skip = ttk.Combobox(self, font = ENTRY_FONT)
        grid_obs_skip['values']= np.arange(1,16,1).tolist()
        grid_obs_skip.current(4) # default

        #speed in seconds of each observation to be plotted
        grid_speed_of_Plot = ttk.Combobox(self, font = ENTRY_FONT)
        grid_speed_of_Plot['values'] = (np.round(np.arange(0.1,2.1,0.1),1) ).tolist()
        grid_speed_of_Plot.current(1) # default

        # Colour palette of the user
        grid_colour_palette= ttk.Combobox(self, font = ENTRY_FONT)
        grid_colour_palette['values']= PLOT_PALLET
        grid_colour_palette.current(0)

        def startPlot():
            """
            This function starts does the initial functions of Starting
            the plot and does the error checking
            """
            lbl_progress.configure(text = "Progress: 0 %") # reset progres
            #making sure that the delay paths are different

        def startGraphing(savePlot):
            """
            This function starts the graphing of the plots

            Parameters
            ----------
            savePlot = boolean
                Inidcates if the plot shoud be saved as a video or not
            """

            #Global variables that needs to be setted
            global COLOUR_PALLET #set global palette
            global OBSERVATION_SKIP #set the observations that need to be skipped
            global PLOTTING_INTERVAL

            #Extract the value of plot quality
            var_plot_qual = str(grid_quality.get()[0]).lower() #Setting extracted string to lowercase

            # Getting pallet option from the input
            var_grid_palette = str(grid_colour_palette.get()[0]).lower()
            #Extracting the colour pallete
            if (var_grid_palette == 'r'): #if red
                COLOUR_PALLET = RED_STATIC_PALETTE
            elif(var_grid_palette == 'b'): #if blue
                COLOUR_PALLET = BLUE_STATIC_PALETTE
            elif(var_grid_palette == 'g'): #if green
                COLOUR_PALLET = GREEN_STATIC_PALETTE


            # Setting the skipping variable
            OBSERVATION_SKIP =int(grid_obs_skip.get())
            #Getting the plotting interval value
            PLOTTING_INTERVAL = int(float(grid_speed_of_Plot.get())*1000) #convert from seconds to ms and then from a float to int

            #call the function to generate the plot after options have been extracted from objects
            generatePlot(savePlot,var_plot_qual)

        def backToStats():
            """
            This function sets the defauls back and takes the user back one
            form
            """
            lbl_progress.configure(text = "Progress: 0 %") #set label back to 0
            controller.show_frame(VesselStats)
            plt.close() #close any open plots


        #Declaring buttons
        btn_plot = ttk.Button(self,text="Start Plot", width = 25,style = "NAV.TButton",
                    command = lambda: startGraphing(False)) #command = funtion to execute
        btn_save_plot = ttk.Button(self,text="Save Plot", width = 25,style = "NAV.TButton",
                        command = lambda:  startGraphing(True)) #command = funtion to execute
        btn_back_stats = ttk.Button(self,text="Back", width = 25,style = "NAV.TButton",
                        command = lambda:  backToStats()) #command = funtion to execute

        #Allignment of the objects on the grid
        grid_speed_of_Plot.grid(row = 8, column = 3)
        grid_quality.grid(row = 2, column =3)
        grid_obs_skip.grid(row = 5, column =3)
        grid_colour_palette.grid(row = 15, column = 3)

        #Label Object allignment
        lbl_col = 0 #colum of labels, sthis varubale can be changed and will be applied to all
        lbl_plot_heading.grid(row = 0, column = 0, columnspan = 12, rowspan = 1, pady = 15)
        lbl_dummy.grid(row = 1, column = lbl_col,sticky = 'e',
                    padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_Quality.grid(row = 2, column = lbl_col, sticky = 'e',
                    padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_obs_skip.grid(row = 5, column = lbl_col,sticky = 'e',
                    padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_plot_speed.grid(row = 8, column = lbl_col,sticky = 'e',
                    padx = BUTTON_PADX, pady = BUTTON_PADY)

        lbl_ColourPalette.grid(row = 15, column = lbl_col,sticky = 'e',
                    padx = BUTTON_PADX, pady = BUTTON_PADY)
        lbl_progress.grid(row = 17, column = 0,columnspan =6,
                    padx = BUTTON_PADX, pady = 5)

        lbl_dummy_2.grid(row = 18, column = lbl_col,sticky = 'e',
                                padx = BUTTON_PADX, pady = BUTTON_PADY)

        #Button Object Allignments
        btn_plot.grid(row = 19,column = 4, padx = 10, pady = 2)
        btn_save_plot.grid(row = 20,column = 4, padx = 10, pady = 2)
        btn_back_stats.grid(row = 21,column = 4, padx = 10, pady = 2)

####--------------------- END OF ANIMATION FRAME ---------------------------

def generatePlot(savePlot, plt_resolution):
    """
    This function will create the animation map of the vessel of the selected
    mmsi. With the option to save the input as a mp4 file in the videos directory

    PARAMETERS:
    ----------
    savePlot: boolean
        default = false
        If the plot should be displayed or if it should be saved as a file

    plt_resolution: str
        Resolution of the basemap plot
    """
    plt.close('all') # close all previous plots
    plt.show(block=False)

    global point #to draw a lone
    global m #basemap

    plt.figure(figsize=(12,7)) #setting the figure size of the plot
    m = Basemap(projection = 'mill',
    llcrnrlon = math.floor(vesselLat_min), #flipping the observations
    urcrnrlon = math.ceil(vesselLat_max), #using ceil & floor to get a nice area and border around the plot
    urcrnrlat = math.ceil(vesselLong_max),
    llcrnrlat = math.floor(vesselLong_min),
    resolution = plt_resolution) #h= high f= full i= intermediate

    #Adding long lat lines
    parallels = np.arange(0.,60,5.)
    m.drawparallels(parallels,labels=[False,True,True,False],fontsize = 14)
    meridians = np.arange(-10.,40.,5.)
    meridians_text = m.drawmeridians(meridians,labels=[True,False,False,True],fontsize = 14)
    m.drawmapboundary(fill_color='#dcf6fa')
    m.drawcoastlines()
    m.fillcontinents(color = '#a8a8a8', lake_color = '#1d6bb5') #fill continents
    m.drawrivers(color = '#1d6bb5')

    x,y = m(0, 0) #starting xy location
    point = m.plot(x, y, 'ro', markersize=5)[0]

    #for saving a unique file name MMSI + CURRENT DATE & TIME
    file_save_date = datetime.datetime.now()
    file_save_date = file_save_date.strftime("%Y-%m-%d_%H_%M_%S")

    if(savePlot == True): #if the plot should be saved
        lbl_progress.configure(text = str("DO NOT CLOSE WINDOW, SAVING VIDEO IN BACKGROUND (max time 8min)"))
        time.sleep(1) #allowing for the above update, ause the program

    frames_calc = int((vessel_observations/OBSERVATION_SKIP)-2)
    if(savePlot != True): #if  we should not save the plot
        global animate_change_col
        animate_change_col = 0 #the variable that changes the colour == reset
        anim = animation.FuncAnimation(plt.gcf(), animate, init_func=init,
                 frames= frames_calc, #amt of observations to plot
                 interval=PLOTTING_INTERVAL, #interval of plots
                 blit=False,
                 repeat = False, #plot should not start over
                 cache_frame_data = False) #do not cache

    else: #if we want to SAVE the plot
        anim = animation.FuncAnimation(plt.gcf(), animate, init_func=init,
                frames=frames_calc,
                interval=PLOTTING_INTERVAL, #interval of plots
                blit=False,
                repeat = False, #plot should not start over
                cache_frame_data = False) #do not cache
        # Saving the animation
        videofile_name  = str(VIDEO_DIRECTORY +"Animation_"+str(mmsi_entry)+"_" +file_save_date +'.mkv')
        anim.save(videofile_name, writer = writer) #use defined writer to save the file

    plt.tight_layout(pad = 4) #Padding to avoid cutoff of titles
    plt.get_current_fig_manager().full_screen_toggle() #make FULL SCREEN
    plt.xlabel("Longitude", labelpad = 25, size = 15) #xlbel
    plt.ylabel("Latitude", labelpad = 15, size = 15)
    plt.title(str("Animation of vessel MMSI - " + str(mmsi_entry)), pad = 15, size = 18)
    plt.show() #show the plot

#####-----------------END OF GENREATE PLOT FUNCTION ----------------------------

def init():
    """
    This function is for the animation fucntion as its initial values
    Returns:
     Empty set
    """
    point.set_data([], [])
    return point,
####--------------------------- END OF INIT FUNCTION ---------------------------

#To get the observations to skip
def vessel_coordinates_plot(i, skip):
    """
    This function returns the observations that needs to be plotted after
    it is skipped by the skipping paramater from the animation function

    PARAMETERS
    ----------
    i: int
        Iteration of the plotting animation
    skip: int
        The amount of observations that needs to be skipped

    RETURNS:
    ----------
    x: np.array
        Array of x coordinates
    y: np.array
        Array of y coordinates
    marker_size: integre
        Size of the observation point
    course_arrow: List
        List of items needed to draw the arrow
    Nav_status: String
        Navigational Status
    """

    course_arrow = [] #this array will indicate the arrow  of the course over ground
    if(skip>0): #if not zero just multiply by i to get each to skip, else plot each i
        i =i*skip

    # For plotting a line between two points
    if(i == 0): #inital starter val
        long_arr = [df_Longitude[i],df_Longitude[i]]
        lat_arr = [df_Latitude[i],df_Latitude[i]]

    else: # get previous point and draw a line between them return as an array
        long_arr = [df_Longitude[i-skip], df_Longitude[i]]
        lat_arr =[df_Latitude[i-skip],df_Latitude[i]]

    #Scaling the arrow
    scaled_sog = df_SOG[i]/np.max(df_SOG)

    course_x, course_y = m(df_Latitude[i],df_Longitude[i])
    course_arrow = [course_x,course_y,df_SOG[i], df_COG[i]]
    Nav_status = df_NAV_status[i]

    #convert back to basemap coordinates
    x,y = m(lat_arr,long_arr)
    # calculating the makerker size, random function
    marker_size=math.ceil(math.sqrt(df_SOG[i]/2)) #make int

    return x,y,marker_size, course_arrow,Nav_status #return related x, y and the marker size

####---------------END OF vessel_coordinates_plot FUNCTION ---------------------

animate_change_col = 0 #for the gradualy colour change
#Animation function
txt_top =  0 #set a inital value for global scope
txt_bottom =  0 #set a inital value for global scope

#####------------------ ANIMATE FUNCTION --------------------------------------
def animate(i):
    """
    This function is resposible for plotting the coordinates on the Basemap map

    PARAMETERS
    ----------
    i: int
        Iteration of plot
    """
    global txt_top, txt_bottom, animate_change_col#label that gets added to display information
    skip_value = i*OBSERVATION_SKIP #Varaible here for less computation, calculated once

    #Location of where the vessel informations should be showed on basemap
    conv_x_top, conv_y_top = m(math.floor(vesselLat_min),(math.ceil(vesselLong_max)))
    conv_x_bottom, conv_y_bottom = m(math.floor(vesselLat_min),(math.floor(vesselLong_min)))

    if(i > 0):
        txt_top.remove() #remove old text from the plot -top
        txt_bottom.remove() #remove old text from the plot

    #Text to be displayed in the animation on top
    display_text_top = (
    "Date: " +str((df_vessel_time[skip_value]).date())+
    "    Time: "+ str((df_vessel_time[skip_value]).time())) #round value

    #text to be displayed at the bottom of the plot
    display_text_bottom = (
    "Long: " + str(round(df_Longitude[skip_value],3)) + #round value
    ",   Lat:" + str(round(df_Latitude[skip_value],3))  +#round value
    "    Speed:    " +    str(df_SOG[skip_value]) +
    "kts,    NAV Status:  " + str(df_NAV_status[skip_value]) )


    #Plotting information label location and text to plot
    txt_top = plt.text(conv_x_top, conv_y_top,display_text_top,size =10,
                    bbox=dict(facecolor = "blue",boxstyle="round",
                    ec="#40d3e3", fc="#40d3e3")) #colour of the label
    txt_bottom = plt.text(conv_x_bottom, conv_y_bottom,display_text_bottom,
                    size =10,bbox=dict(facecolor = "blue",boxstyle="round",
                    ec="#40d3e3", fc="#40d3e3")) #colour of the label

    col_change = int(int(vessel_observations/(OBSERVATION_SKIP)-1)/150)

    if col_change == 0:  #incase a MMSI hass less than 151 observations -- colour will remain static
        animate_change_col = 1
    else:
        if(((i % col_change) == 0) and animate_change_col < 149 ):
            animate_change_col += 1

    #progress label calcualtion
    progress_perc = int( (i/(vessel_observations/OBSERVATION_SKIP-2))*100)
    lbl_progress.configure(text = str("Progress: "+
                str(progress_perc) + " %"))
    x,y,vessel_marker_size, course_vessel_array, vesselNavStat = vessel_coordinates_plot(i, OBSERVATION_SKIP) #get values for the current plot

    """
    The following code will add arrows to the map each 10th observation
    """
    sog_vessel = course_vessel_array[2]
    cog_vessel = course_vessel_array[3]
    cog_x = course_vessel_array[0]
    cog_y = course_vessel_array[1]

    #Indicate stationary times
    #at anchor, or if it is moored. If the vessel is not even one of these
    #then check if the speed == 0, if true make a dot
    if (vesselNavStat == "At anchor" or vesselNavStat == "Moored"):
        circle = plt.Circle((cog_x,cog_y),1000, color = '#9d00ff', fill = True)
        plt.gcf().gca().add_artist(circle)
    elif(sog_vessel == 0): #0.5 speed wat which a boat is slow
        circle = plt.Circle((cog_x,cog_y),1000, color = '#9d00ff', fill = True)
        plt.gcf().gca().add_artist(circle)

    if(i%10 == 0): #plot every 10th arrow
        scaled_speed = getArrowSize(sog_vessel)
        arrow_radius = scaled_speed #speed^4 / 2, to have an exponential scale, and divide by 2 to scale down
        arrow_angle = (cog_vessel-90)*(-1) #adjusting the scale of the basmap to compas degrees
        #cog == course over ground in degrees, needs to be converted because basemap 0° is other way aroun(anti clock wize)

        angle_rad = arrow_angle * math.pi/180 #conver to radiants
        arrow_head_dimentions = scaled_speed*0.7#arrow head dimentions, also related to the speed
        plt.arrow(cog_x,cog_y,
                        (arrow_radius)*math.cos(angle_rad), #drawing the arrow (get correspondin coordinate values)
                        (arrow_radius)*math.sin(angle_rad),
                        head_width = arrow_head_dimentions, #width of the arrow head
                        head_length = 100+arrow_head_dimentions, #lenght of the arrow head
                        linewidth = 2, #arrow line width
                        fc = COLOUR_PALLET[animate_change_col], #arrow colours
                        ec = COLOUR_PALLET[animate_change_col])

    m.plot(x,y,"o-", linewidth = 1,markersize=vessel_marker_size,
     c = COLOUR_PALLET[animate_change_col]) #newest path colour
#####-------- END of ANIMATE FUNCTION -------------------------

app = GISVizTool() #define the class
app.geometry("800x520") #making tkinter window size
app.mainloop() #Tkinter code
