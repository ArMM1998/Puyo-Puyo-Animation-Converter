import os, sys, struct, json
from fractions import Fraction

flag_3ds = False
ds_flag = False
mobile_flag = False
mode = "to_json"
name_order_flag = False
debug = False
endianness = "<"

def log(string):
    if debug:
        if type(string) == dict or type(string) == list :
            print(json.dumps(string, indent=4))
        else:
            print(string)

aspect_ratio_dict = {1.7647058963775635 : "480x272",        #PSP
                     1.666748046875 : "400x240",            #3DS top screen
                     1.333251953125 : "256x192",            #3DS bottom screen         
                     1.4285714626312256 : "640x448",        #Wii 4:3
                     1.7763158082962036 : "811x456",        #Wii 16:9
                     0.5625 : "720x1280",                   #Mobile
                     0.5633803009986877 : "720x1280",       #Mobile - Newer versions of Quest?
                     0.6666666865348816 : "720x1280",       #Taller Mobile (?) Puyo touch
                     1.3333333730697632 : "256x192",        #unk 4:3, possibly DS
                     1.7777777910232544 : "1280x720"}       #unk 16:9

def getScreenSize(aspect_ratio):
    screen_size = aspect_ratio_dict[aspect_ratio]
    if screen_size == "256x192" and flag_3ds:
        screen_size = "320x240"
    return screen_size

#Get the command arguments
try:
    #input file
    input_file = sys.argv[1:][0]
    #determine the output file path
    if input_file == "-help" or input_file == "-h" or input_file == "-?":
        raise
    if input_file.endswith(".json"):
        output_file = input_file[:-5] #remove .json from the filename
    else:
        output_file = input_file + ".json"
    
    #Get arguments
    arg_index = 0
    for argument in sys.argv[1:]:
        #output
        if argument.find("-o") != -1:
            output_file = sys.argv[1:][arg_index+1]
        
        #ds/3ds file
        if argument.find("-ds") != -1 or argument.find("-3ds") != -1:
            if argument.find("-3ds") != -1:
                flag_3ds = True
            ds_flag = True
        
        #puyo quest / puyo touch
        if argument.find("-m") != -1:
            ds_flag = False #just in case, since mobile =/= ds
            mobile_flag = True
        arg_index += 1
        
        #name order blegh
        if argument.find('--name_order') != -1:
            name_order_flag = True
        
        #debug
        if argument.find('--debug') != -1 or argument.find('-dbg') != -1:
            debug = True
        
    #Now let's determine if we're converting from json or to json
    if input_file.find(".json") != -1:
        mode = "to_anim"
    else:
        mode = "to_json"
        #What if the output doesn't have .json?
        log("Did you forget to add .json to the output? I'll add it instead.")
        if output_file.find(".json") == -1:
            output_file += ".json"

except:
    print("Correct usage: \n\npuyo_anim.py [input] [options]\n\nAvailable options:\n        '-o' Output file. This will be determined automatically if not set.")
    print("        '-ds' Converting to or from a Nintendo DS animation file.\n        '-3ds' Converting to or from a Nintendo 3DS animation file.\n        '-m' Converting to or from a mobile file. This includes Puyo Puyo Quest and Puyo Puyo Touch.")
    print("        '--name_order' Keep the order of the elements.\n                       Some animation files have an oddly specific order for it's names that the games can be hardcoded to expect.\n                       Recommended if you're editing UI or Manzai animations, but not for general animation editing, like cut-ins.")
    print("        '-dbg' | '--debug' Enable printing debug info")
    print("Example:\n        puyo_anim.py title.snc -o title.snc.json\n        Converts from an animation file to a .json")
    print("\nThe conversion will depend on the file extension of the input.\nIf the extension is '.json', then it will convert the json to it's corresponding animation file format.\nIf it has any extension other than 'json', or no extension at all, it will treat the input file as an animation file.")
    exit()

def bytesToInt(offset, length):
    if length == 4:
        data_type = "i"
    if length == 8:
        data_type = "q"
    value = anim_file_data[offset].to_bytes(1, "big")
    for i in range(length-1):
        value += anim_file_data[offset + i +1].to_bytes(1, "big")
        
    value = struct.unpack(endianness + data_type,value)[0]
    
    log("Value at offset " + str(offset) + " converted to int " + str(value) + " length in bytes: " + str(length))
    
    return value

def bytesToFloat(offset):
    data_type = "f"
    value = anim_file_data[offset].to_bytes(1, "big")
    #Handle DS floats
    if ds_flag:
        value = bytesToInt(offset, 4)/2 **12
    else:
        for i in range(3):
            value += anim_file_data[offset + i +1].to_bytes(1, "big")
            
        value = struct.unpack(endianness + data_type,value)[0]
        
    log("Value at offset " + str(offset) + " converted to float " + str(value))
    
    return value

def bytesToPointer(offset):
    if mobile_flag:
        length = 8
    else:
        length = 4
    pointer_value = bytesToInt(offset, length)
    
    pointer_value += alignment
    
    log("Value at offset " + str(offset) + " is a pointer to " + str(pointer_value))
    return((pointer_value, length + offset))

def get_string(offset, length = False):
    string = b''
    while True:
        if anim_file_data[offset] == 0:
            break
        elif length != False:
            if len(string) == length:
                break
        string += anim_file_data[offset].to_bytes(1, "big")
        offset += 1
        
    return string.decode("shift-jis")

def packRGBA(rgba_dict, f, byte_order = False):
    rgba_list = []
    if byte_order == False:
        byte_order = endianness
    if byte_order == "<":
        f.write(struct.pack(endianness + "B", rgba_dict["alpha"]))
        f.write(struct.pack(endianness + "B", rgba_dict["blue"]))
        f.write(struct.pack(endianness + "B", rgba_dict["green"]))
        f.write(struct.pack(endianness + "B", rgba_dict["red"]))
    if byte_order == ">":
        f.write(struct.pack(endianness + "B", rgba_dict["red"]))
        f.write(struct.pack(endianness + "B", rgba_dict["green"]))
        f.write(struct.pack(endianness + "B", rgba_dict["blue"]))
        f.write(struct.pack(endianness + "B", rgba_dict["alpha"]))
        

def packInt(integer, length, byte_order = False):
    if byte_order == False:
        byte_order = endianness
    if length == 4:
        data_type = "i"
    if length == 8:
        data_type = "q"
    return(struct.pack(byte_order + data_type, integer))

def packFloat(floating, byte_order = False):
    if byte_order == False:
        byte_order = endianness
    if ds_flag:
        return(struct.pack(byte_order + "i", floatToFixed(floating)))
    else:
        return(struct.pack(byte_order + "f", floating))

def floatToFixed(number):
    number = int(number* 4096)
    return number

def padString(text, block_size = 4):
    pad_size = block_size - len(text)% block_size
    fit_text = text + (" "*pad_size)
    return (fit_text)

def packPointer(number, byte_order = False):
    if byte_order == False:
        byte_order = endianness
    if mobile_flag:
        return(struct.pack(byte_order + "q", number))
    else:
        return(struct.pack(byte_order + "i", number))
        
#debug shit i guess
log("input file: " + input_file)
log("output file: " + output_file)
log("DS flag: " + str(ds_flag))
log("3DS flag: " + str(flag_3ds))
log("Mobile flag: " + str(mobile_flag))
log("mode: " + mode + "\n\n")

########## Misc functions #########


def getEdgeList(hierarchy):
    #0 can't have parent as far as i'm aware
    #hierarchy[0] = -1
    adjacency = {-1:[0]}
    for element in range(len(hierarchy)):
        adjacency[element] = []
        
    #(adjacency)
    elm_index = 0
    for element in hierarchy:
        try:
            if elm_index not in adjacency[element]:
                adjacency[element].append(elm_index)
        except:
            if elm_index not in adjacency[-1]:
                adjacency[-1].append(elm_index)
        elm_index += 1
    
    edge =  [[None,None] for _ in range(len(hierarchy))]
    scope_list = [-1]
    elements_added = []
    current_element=-1
    #Check if the element has a child
    while len(scope_list) != 0:
        if current_element == -1:
            if len(adjacency[-1]) != 0:
                current_element = adjacency[-1][0]
                adjacency[-1].pop(0)
        #check if the current element's children list is not empty
        if len(adjacency[current_element]) != 0:
            #current child
            child = adjacency[current_element][0]
            #add child to edge list for the current element.
            if adjacency[current_element][0] not in elements_added:
                edge[current_element][0] = adjacency[current_element][0]
                elements_added.append(adjacency[current_element][0])
            #add current element to scope list, so we can check for further children later.
            scope_list.append(current_element)
            adjacency[current_element].pop(0)
            #make current element the child, so we can check if it has any children.
            current_element = child
        else:
            #add -1 to the current element's child
            if edge[current_element][0] == None:
                edge[current_element][0] = -1
            
            #current scope
            current_scope = scope_list[len(scope_list)-1]
            #check if there's another element in the current scope
            if len(adjacency[current_scope]) != 0:
                #get the new child
                new_child = adjacency[current_scope][0]
                #remove it.
                adjacency[current_scope].pop(0)
                if new_child not in elements_added:
                    #add it to edge list of the current element.
                    edge[current_element][1] = new_child
                    elements_added.append(new_child)
                #make it the new current element
                current_element = new_child
            else:
                #add -1 to edge
                edge[current_element][1] = -1
                current_element = scope_list[len(scope_list)-1]
                #remove last element from scope
                scope_list.pop()
    return(edge)

def sortMotion(dict):
    return ["hide", "posx", "posy", "angle", "scalex", "scaley", "sprite_index", "rgba", "rgba_tl", "rgba_bl", "rgba_tr", "rgba_br", "audio_cue?" , "3d_depth", "unk_motion"].index(dict['Motion'])

motion_names = {1 : "hide",
                2 : "posx",
                4 : "posy",
                8 : "angle",
                16: "scalex",
                32: "scaley",
                64: "sprite_index",
                128 : "rgba",
                256 : "rgba_tl",
                512 : "rgba_bl",
                1024 : "rgba_tr",
                2048 : "rgba_br",
                4096 : "audio_cue?",
                8192 : "3d_depth",
                16384 : "unk_motion",
                "hide"         : 1    ,
                "posx"         : 2    ,
                "posy"         : 4    ,
                "angle"        : 8    ,
                "scalex"       : 16   ,
                "scaley"       : 32   ,
                "sprite_index" : 64   ,
                "rgba"         : 128  ,
                "rgba_tl"      : 256  ,
                "rgba_bl"      : 512  ,
                "rgba_tr"      : 1024 ,
                "rgba_br"      : 2048 ,
                "audio_cue?"   : 4096 ,
                "3d_depth"     : 8192 ,
                "unk_motion"   : 16384
                }


def get_powers(number):
    powers = (16384, 8192, 4096, 2048, 1024 , 512, 256, 128, 64, 32, 16, 8,4, 2, 1)
    which_power = 0
    power_list = []
    while True:
        if (number / powers[which_power]).is_integer():
            power_list.append(powers[which_power])
            number -= powers[which_power]
            which_power = 0
            if number < 1:
                break
        else:
            which_power += 1
    return power_list
    

def four_bytes_to_RGBA(offset):   #convert the 4 next bytes to an float
    if endianness == "<":
        rgba = {"red" : anim_file_data[offset+3], "green" : anim_file_data[offset+2], "blue" : anim_file_data[offset+1],"alpha" : anim_file_data[offset]}
    else:
        rgba = {"red" : anim_file_data[offset], "green" : anim_file_data[offset+1], "blue" : anim_file_data[offset+2],"alpha" : anim_file_data[offset+3]}
    return rgba

def get_render_method(offset):
    if endianness == ">":
        render = {"dodge_blend": anim_file_data[offset+3],
                  "unknown_1" : anim_file_data[offset+2],
                  "unknown_2" : anim_file_data[offset+1],}
    else:
        render = {"dodge_blend": anim_file_data[offset],
                  "unknown_1" : anim_file_data[offset+1],
                  "unknown_2" : anim_file_data[offset+2],}
    return render

def get_hierarchy(offset, num_of_elms):
    hierarchy = []
    for i in range(num_of_elms):
        hierarchy.append([bytesToInt(offset+i*8, 4), bytesToInt(offset+4+i*8, 4)])
    
    parenting = getParentData(hierarchy)
    print(parenting)
    hierarchy = []
    for a in parenting:
        if a == None:
            hierarchy.append(-1)
        else:
            hierarchy.append(a)
    
    return hierarchy

def getParentData(elementDataIn):
    no_loop = []
    parentData = [None] * len(elementDataIn)
    elementData = elementDataIn.copy()
    currentId = 0
    for entry in elementData:
        entry.append(currentId)
        currentId += 1
    newElementData = []
    #print(elementDataIn)
    while len(elementData) != 0:
        for entry in elementData:
            if entry[0] != -1:
                if parentData[entry[0]] is None:
                    parentData[entry[0]] = entry[2]
                else:
                    newElementData.append(entry)  # Append to process later
            if entry[1] != -1:
                if parentData[entry[2]] is None:
                    newElementData.append(entry)  # Append to process later
                else:
                    parentData[entry[1]] = parentData[entry[2]]
        elementData = newElementData
        newElementData = []
        
    return parentData





#Anim to json
if mode == "to_json":
    anim_file_data = open(input_file, "r+b").read()
    try:
        ncsc = get_string(32,4)
    except:
        print(input_file, "not anim")
        #input("not anim")
        exit()
    if get_string(32,4) != "nCSC" :
        print(input_file, "not anim")
        #input("not anim")
        exit()
    log("starting conversion to json")
    
    #determine endianness
    if bytesToInt(8,4) == 1:
        endianness = "<"
    else:
        endianness = ">"
    log("byte order: " + endianness)
    
    #determine alignment
    #For now it seems to be 32 always, but i can change it later here if that's not the case.
    alignment = bytesToInt(12,4)
    log("alignment: " + str(alignment) )
    
    
    #Let's begin!!!!!!!
    #Let's first get the relevant header data.
    magic = get_string(0,4)
    
    #The unknown patterns are always here.
    data_offset = 68
    num_unk_pattern = bytesToInt(data_offset,4)
    data_offset += 4
    unk_pattern_off, data_offset = bytesToPointer(data_offset)
    
    #sprite crops
    num_sprite_crops = bytesToInt(data_offset,4)
    data_offset += 4
    sprite_crops_off, data_offset = bytesToPointer(data_offset)
    
    #get element banks
    num_elem_banks = bytesToInt(data_offset,4)
    data_offset += 4
    elem_banks_off, data_offset = bytesToPointer(data_offset)
    
    #element names
    num_elem_names = bytesToInt(data_offset,4)
    data_offset += 4
    elem_names_off, data_offset = bytesToPointer(data_offset)
    
    #animations
    num_anims = bytesToInt(data_offset,4)
    data_offset += 4
    anims_off, data_offset = bytesToPointer(data_offset)
    
    #animation names
    anim_names_off, data_offset = bytesToPointer(data_offset)
    
    #aspect ratio
    aspect_ratio = Fraction(bytesToFloat(data_offset)).limit_denominator()
    screen_size = getScreenSize(bytesToFloat(data_offset))
    data_offset += 4
    log("unk patterns: " + str(num_unk_pattern))
    log("sprite crops: " + str(num_sprite_crops))
    log("element banks: " + str(num_elem_banks))
    log("elements: " + str(num_elem_names))
    log("animations: " + str(num_anims))
    log("screen size: " + str(screen_size))
    
    #animation lengths
    anim_len_off, data_offset = bytesToPointer(data_offset)
    
    #Header data is over. Now let's start storing the data.
    
    #Unknown Patterns
    data_offset = unk_pattern_off
    unk_pattern_list = []
    for i in range(num_unk_pattern):
        unk_pattern_list.append((bytesToFloat(data_offset), bytesToFloat(data_offset+4)))
        data_offset += 8
    log("\nunknown patterns:")
    log(unk_pattern_list)
    
    data_offset = sprite_crops_off
    sprite_crop_list = []
    #Sprite Crops:
    for i in range(num_sprite_crops):
        texture = bytesToInt(data_offset,4)
        data_offset +=4
        top_left_X = bytesToFloat(data_offset)
        data_offset +=4
        top_left_Y = bytesToFloat(data_offset)
        data_offset +=4
        bottom_right_X = bytesToFloat(data_offset)
        data_offset +=4
        bottom_right_Y = bytesToFloat(data_offset)
        data_offset +=4
        
        sprite_crop_list.append({"texture": texture,
                                 "top_left_X": top_left_X,
                                 "top_left_Y": top_left_Y,
                                 "bottom_right_X": bottom_right_X,
                                 "bottom_right_Y": bottom_right_Y})
    log("\nsprite crops")
    for i in sprite_crop_list:
        log(i)
    
    #element banks (uh oh)
    data_offset = elem_banks_off
    element_banks = []
    #for every bank of elements
    for bank in range(num_elem_banks):
        num_elem_in_bank = bytesToInt(data_offset, 4)
        data_offset += 4
        elem_list_off, data_offset = bytesToPointer(data_offset)
        log("unknown int(?) value at " + str(data_offset) + " : " + str(bytesToInt(data_offset, 4)))
        data_offset += 4
        hierarchy_off, data_offset = bytesToPointer(data_offset)
        element_bank = []
        hierarchy = get_hierarchy(hierarchy_off, num_elem_in_bank)
        bank_off = elem_list_off
        #Let's start storing the element data
        for a in range(num_elem_in_bank):
            element_offset, bank_off = bytesToPointer(bank_off)
            element = {}
            element["Index"] = a
            element["Name"] = "" #dummy for now
            element["Parent"] = hierarchy[a]
            element["Unknown Flag 0"] = bytesToInt(element_offset,4)
            element_offset += 4
            element["Render Flag"] = bytesToInt(element_offset,4)
            element_offset += 4
            element["Unknown Flag 1"] = bytesToInt(element_offset,4)
            
            #2D Polygon
            element_offset += 4
            TL_X = bytesToFloat(element_offset)
            element_offset += 4
            TL_Y = bytesToFloat(element_offset)
            element_offset += 4
            BL_X = bytesToFloat(element_offset)
            element_offset += 4
            BL_Y = bytesToFloat(element_offset)
            element_offset += 4
            TR_X = bytesToFloat(element_offset)
            element_offset += 4
            TR_Y = bytesToFloat(element_offset)
            element_offset += 4
            BR_X = bytesToFloat(element_offset)
            element_offset += 4
            BR_Y = bytesToFloat(element_offset)
            element_offset += 4
            element["2D Polygon"] = [TL_X, TL_Y, BL_X, BL_Y, TR_X, TR_Y, BR_X, BR_Y]
            
            element["Unknown Values"] = [bytesToInt(element_offset, 4)]
            element_offset += 4
            
            elem_settings_off, element_offset = bytesToPointer(element_offset)
            element["Unknown Values"].append(bytesToInt(element_offset, 4))
            element_offset += 4
            element["Render Settings"] = get_render_method(element_offset)
            element_offset += 4
            num_element_sprites = bytesToInt(element_offset, 4)
            element_offset += 4
            element_sprites_off, element_offset = bytesToPointer(element_offset)
            sprite_list = []
            for i in range(num_element_sprites):
                if debug:
                    if bytesToInt(element_sprites_off, 4) not in sprite_list: #For the sake of debugging, let's stop duplicates
                        sprite_list.append(bytesToInt(element_sprites_off, 4))
                else:
                    sprite_list.append(bytesToInt(element_sprites_off, 4))
                element_sprites_off += 4
            element["Sprite List"] = sprite_list
            element_settings = {}
            
            element_settings["hide"] = bytesToInt(elem_settings_off, 4)
            elem_settings_off +=4
            element_settings["posx"] = bytesToFloat(elem_settings_off)
            elem_settings_off +=4
            element_settings["posy"] = bytesToFloat(elem_settings_off)
            elem_settings_off +=4
            element_settings["angle"] = bytesToFloat(elem_settings_off)
            elem_settings_off +=4
            element_settings["scalex"] = bytesToFloat(elem_settings_off)
            elem_settings_off +=4
            element_settings["scaley"] = bytesToFloat(elem_settings_off)
            elem_settings_off +=4
            element_settings["sprite_index"] = int(bytesToFloat(elem_settings_off))
            elem_settings_off +=4
            element_settings["rgba"] = four_bytes_to_RGBA(elem_settings_off)
            elem_settings_off +=4
            element_settings["rgba_tl"] = four_bytes_to_RGBA(elem_settings_off)
            elem_settings_off +=4
            element_settings["rgba_bl"] = four_bytes_to_RGBA(elem_settings_off)
            elem_settings_off +=4
            element_settings["rgba_tr"] = four_bytes_to_RGBA(elem_settings_off)
            elem_settings_off +=4
            element_settings["rgba_br"] = four_bytes_to_RGBA(elem_settings_off)
            elem_settings_off +=4
            
            element_settings["audio_cue?"] = bytesToInt(elem_settings_off, 4)
            elem_settings_off +=4
            
            element_settings["3d_depth"] = bytesToInt(elem_settings_off, 4)
            elem_settings_off +=4
            
            element_settings["unk_motion"] = bytesToInt(elem_settings_off, 4)
            elem_settings_off +=4
            
            # element_settings["unk_settings"] = []
            # for i in range(3): #get last 3 unk values
                # element_settings["unk_settings"].append(bytesToInt(elem_settings_off, 4))
                # elem_settings_off +=4
            element["Default Settings"] = element_settings
            #add the rest of the unk values as INT because i don't know what else they are... They're usually 00 00 00 00 .
            element["Unknown Values"].append(bytesToInt(element_offset, 4))
            element_offset += 4
            #Name order?
            
            #The rest seem to be offsets since they get larger if mobile or not (?) 
            #I don't know which one is the integer and which ones are the pointer.
            unk_off0, element_offset = bytesToPointer(element_offset)
            unk_off1, element_offset = bytesToPointer(element_offset)

            element_bank.append(element)
        element_banks.append(element_bank)
        log(element_bank)
    #Let's now get the names for each element.
    data_offset = elem_names_off
    for i in range(num_elem_names):
        name_offset, data_offset = bytesToPointer(data_offset)
        bank_index = bytesToInt(data_offset, 4)
        data_offset += 4
        elm_index = bytesToInt(data_offset, 4)
        data_offset += 4
        element_banks[bank_index][elm_index]["Name"] = get_string(name_offset)
        if name_order_flag:
            element_banks[bank_index][elm_index]["Name Index"] = i
        log(element_banks[bank_index][elm_index])
        
    
    animations = []
    #Time to store animations
    data_offset = anims_off
    for anim_num in range(num_anims):
        bank_num = bytesToInt(data_offset, 4)
        data_offset += 4
        anim_bank_off, data_offset = bytesToPointer(data_offset)
        log("animation " + str(anim_num) + " with " + str(bank_num) + " element bank(s). offset: " + str(anim_bank_off))
        animation_element_bank_list = []
        for element_bank in range(bank_num): #for element bank in animation
            num_elems = bytesToInt(anim_bank_off, 4)
            anim_bank_off+=4
            anim_off, anim_bank_off = bytesToPointer(anim_bank_off)
            log("bank " + str(element_bank) + " with " + str(num_elems) + " element(s) - Current offset:" + str(anim_bank_off))
            animation_list = []
            
            for element in range(num_elems):
               #Store motion types 
                motions = bytesToInt(anim_off, 4)
                anim_off += 4
                log("motion_int : " + str(motions) + " - offset :" + str(anim_off))
                keyframelist_offset, anim_off = bytesToPointer(anim_off)
                motion_list = []
                if motions != 0:
                    log(motions)
                    motions = get_powers(motions)
                    for motion in motions:
                        motion_list.append(motion_names[motion])
                
                element_animation = []
                #for motion in motion_list:
                for motion in motion_list:
                    loop_value = bytesToInt(keyframelist_offset, 4)
                    keyframelist_offset += 4
                    
                    #GetKeyframes
                    num_keyframes = bytesToInt(keyframelist_offset, 4)
                    keyframelist_offset += 4
                    keyframe_offset, keyframelist_offset = bytesToPointer(keyframelist_offset)
                    
                    log(keyframe_offset)
                    keyframe_list = []
                    for keyframe in range(num_keyframes):
                        keyframe = {}
                        keyframe["timestamp"] = bytesToInt(keyframe_offset, 4)
                        keyframe_offset+=4
                        if motion.find("rgba") != -1:
                            keyframe["data"] = four_bytes_to_RGBA(keyframe_offset)
                        elif motion.find("hide") != -1 or motion.find("3d_depth") != -1:
                            keyframe["data"] = bytesToInt(keyframe_offset, 4)
                        else:
                            keyframe["data"] = bytesToFloat(keyframe_offset)
                        keyframe_offset+=4
                        keyframe["tweening"] = bytesToInt(keyframe_offset, 4)
                        keyframe_offset+=4
                        keyframe["ease_in"] = bytesToFloat(keyframe_offset)
                        keyframe_offset+=4
                        keyframe["ease_out"] = bytesToFloat(keyframe_offset)
                        keyframe_offset+=4
                        keyframe["unk"] = bytesToFloat(keyframe_offset)
                        keyframe_offset+=4
                        keyframe_list.append(keyframe)
                    element_animation.append({"Motion" : motion, "Loop" : loop_value, "Keyframes" : keyframe_list})
                animation_list.append({"Index" : element, "Animations" : element_animation})
            animation_element_bank_list.append(animation_list)
        #log(animation_element_bank_list)
        
        temp_name_off = anim_names_off
        for anim in range(num_anims):   
            name_offset, temp_name_off = bytesToPointer(temp_name_off)
            name_index = bytesToInt(temp_name_off, 4)
            temp_name_off+= 4
            if name_index == anim_num:
                anim_name = get_string(name_offset)
                log(anim_name)
        anim_len = (bytesToFloat(anim_len_off), bytesToFloat(anim_len_off+4))
        anim_len_off += 8
        animations.append({"Name" : anim_name, "Length Range" : anim_len, "Element Banks" : animation_element_bank_list})
    #log(animations)
    
    #Misc info i guess
    misc_info = {"Header Magic" : magic,
                 "Aspect Ratio" : str(aspect_ratio),
                 "Screen Size" : screen_size,
                 "Byte Order" : endianness, 
                 }
    
    final_json = {"Misc. Info": misc_info, "Unk. Patterns" : unk_pattern_list, "Sprite Crops" : sprite_crop_list, "Element Banks" : element_banks, "Animations" : animations}
    
    output_json = open(output_file, 'w', encoding = "utf-8")
    output_json.write("")
    json.dump(final_json, output_json, indent=4, ensure_ascii=False)    

if mode == "to_anim":
    log("starting conversion to anim")
    json_data = json.load(open(input_file, 'r'))
    endianness = json_data["Misc. Info"]["Byte Order"]
    log("Byte Order: " + str(endianness))
    weird_pointer = 88
    if mobile_flag:
        data_offset = 116
    else:
        data_offset = 88
    pointer_list = [] #Will be used later
    with open(output_file, "wb") as f:
        f.write(bytes("nCSC", 'UTF-8')) #Write nCSC magic
        f.write(bytes(4)) #For now let's skip this spot as it's the length of the data.
        f.write(packInt(16, 4))
        f.write(packInt(0, 4))
        f.write(packInt(2, 4))
        #Mostly unknown floats that don't seem to have any effect when changed, so i'll keep the common values among files
        f.write(packFloat(0)) 
        f.write(packFloat(60)) 
        f.write(packFloat(0)) 
        f.write(packFloat(60)) 
        
        #Mostly header for now -
        #UnknownPatterns
        f.write(packInt(len(json_data["Unk. Patterns"]), 4)) 
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        data_offset += len(json_data["Unk. Patterns"])*8
        weird_pointer += len(json_data["Unk. Patterns"])*8
        #SpriteCrops
        f.write(packInt(len(json_data["Sprite Crops"]), 4)) 
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        data_offset += len(json_data["Sprite Crops"])*20
        weird_pointer += len(json_data["Sprite Crops"])*20
        #Element Banks
        f.write(packInt(len(json_data["Element Banks"]), 4)) 
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        #Account for each element bank pointer - Already checked
        if mobile_flag:
            data_offset += len(json_data["Element Banks"])*24
            weird_pointer += len(json_data["Element Banks"])*16
        else:
            data_offset += len(json_data["Element Banks"])*16
            weird_pointer += len(json_data["Element Banks"])*16
            
        #Element names
        amount_of_elements = 0
        for group in json_data["Element Banks"]:
            for element in group:
                amount_of_elements+=1
        f.write(packInt(amount_of_elements, 4)) 
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        #Account for each element name pointer - Already checked
        if mobile_flag:
            data_offset += amount_of_elements*16
            weird_pointer += amount_of_elements*12
        else:
            data_offset += amount_of_elements*12
            weird_pointer += amount_of_elements*12
        #Animations
        f.write(packInt(len(json_data["Animations"]), 4)) 
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        #Account for each animation pointer - Already Checked
        if mobile_flag:
            data_offset += len(json_data["Animations"])*12
            weird_pointer += len(json_data["Animations"])*8
        else:
            data_offset += len(json_data["Animations"])*8
            weird_pointer += len(json_data["Animations"])*8
        #Animation Names
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        #Account for each animation name pointer
        if mobile_flag:
            data_offset += len(json_data["Animations"])*12
            weird_pointer += len(json_data["Animations"])*8
        else:
            data_offset += len(json_data["Animations"])*8
            weird_pointer += len(json_data["Animations"])*8
            
        #Aspect Ratio
        aspect_ratio = int(json_data["Misc. Info"]["Aspect Ratio"].split("/")[0]) / int(json_data["Misc. Info"]["Aspect Ratio"].split("/")[1])
        f.write(packFloat(aspect_ratio))
        
        #Animation Lengths pointer
        pointer_list.append(f.tell())
        f.write(packPointer(data_offset))
        
        #Account for animation lengths
        data_offset += len(json_data["Animations"])*8
        weird_pointer += len(json_data["Animations"])*8
        ##HEADER DONE!!
        
        #Unk patterns
        for unk_pattern in json_data["Unk. Patterns"]:
            f.write(packFloat(unk_pattern[0]))
            f.write(packFloat(unk_pattern[1]))
        
        #Sprite Crops
        for crop in json_data["Sprite Crops"]:
            f.write(packInt(crop["texture"],4))
            f.write(packFloat(crop["top_left_X"]))
            f.write(packFloat(crop["top_left_Y"]))
            f.write(packFloat(crop["bottom_right_X"]))
            f.write(packFloat(crop["bottom_right_Y"]))
            
        #Element bank pointers D:
        for bank in json_data["Element Banks"]:
            f.write(packInt(len(bank),4))
            pointer_list.append(f.tell())
            f.write(packPointer(data_offset))
            
            #Account for each element pointer in bank
            if mobile_flag:
                data_offset += len(bank)*8
                weird_pointer += len(bank)*4
            else:
                data_offset += len(bank)*4
                weird_pointer += len(bank)*4
                
            f.write(packInt(0,4)) #Unknown 0 value between the two element pointers (?)
            pointer_list.append(f.tell())
            f.write(packPointer(data_offset))
            #I need to account for each element in the bank for it's hierarchy...
            for element in bank:
                data_offset += 8 #account for 2 values per element for hierarchy.
                weird_pointer += 8
        
        #does name order matter?
        if "Name Index" in json_data["Element Banks"][0][0].keys():
            name_index = True
        else:
            name_index = False
        
        # Element Name pointers
        temp_name_order = {}
        bank_index = 0
        if name_index:
            for bank in json_data["Element Banks"]:
                element_index = 0
                for element in bank:
                    temp_name_order[element["Name Index"]] = (bank_index,element_index)
                    element_index+= 1
                bank_index += 1
        #order doesn't matter, who cares
        else:
            cnt = 0
            for bank in json_data["Element Banks"]:
                element_index = 0
                for element in bank:
                    temp_name_order[cnt] = (bank_index,element_index)
                    element_index+= 1
                    cnt += 1
                bank_index += 1
        #log(temp_name_order)
        
        #Element name pointers here
        for i in range(amount_of_elements):
            bank = temp_name_order[i][0]
            index = temp_name_order[i][1]
            pointer_list.append(f.tell())
            f.write(packPointer(data_offset))
            name_length = len(padString(json_data["Element Banks"][bank][index]["Name"], 4))
            data_offset+= name_length
            weird_pointer += name_length
            f.write(packInt(bank, 4))
            f.write(packInt(index, 4))
        
        #Animation pointers
        for anim in json_data["Animations"]:
            number_of_groups = len(anim["Element Banks"])
            #anim_index = json_data["Animations"].index(anim)
            f.write(packInt(number_of_groups, 4))
            pointer_list.append(f.tell())
            f.write(packPointer(data_offset))
            #account for animation pointers
            if mobile_flag:
                data_offset += number_of_groups*12
                weird_pointer += number_of_groups*8
            else:
                data_offset += number_of_groups*8
                weird_pointer += number_of_groups*8
        
        #Animation name pointers
        for anim in json_data["Animations"]:
            anim_index = json_data["Animations"].index(anim)
            name_length = len(padString(anim["Name"], 4))
            pointer_list.append(f.tell())
            f.write(packPointer(data_offset))
            data_offset += name_length
            weird_pointer += name_length
            f.write(packInt(anim_index, 4))
        
        #Animation lengths
        for anim in json_data["Animations"]:
            f.write(packFloat(anim["Length Range"][0]))
            f.write(packFloat(anim["Length Range"][1]))
        
        #Element pointers + hierarchy
        for bank in json_data["Element Banks"]:
            hierarchy = []
            for element in bank:
                hierarchy.append(element["Parent"])
                edge_list = getEdgeList(hierarchy)
                pointer_list.append(f.tell())
                f.write(packPointer(data_offset))
                #account for element length.
                if mobile_flag:
                    data_offset += 96
                    weird_pointer += 80
                else:
                    data_offset += 80
                    weird_pointer += 80
            for i in edge_list:
                f.write(packInt(i[0], 4))
                f.write(packInt(i[1], 4))
                
        #NAMES
        for i in range(len(temp_name_order)):
            #element_name = padString(json_data["Element Banks"][temp_name_order[name][0]][temp_name_order[name][1]]["Name"])
            element_name = padString(json_data["Element Banks"][temp_name_order[i][0]][temp_name_order[i][1]]["Name"])
            #log(element_name.replace(" ", "@"))
            f.write(bytes(element_name, "shift-jis").replace(b' ', b'\x00'))
            
        #Element bank Pointers for animations
        for anim in json_data["Animations"]:
            for bank in anim["Element Banks"]:
                num_of_elems = len(bank)
                f.write(packInt(num_of_elems, 4))
                pointer_list.append(f.tell())
                f.write(packPointer(data_offset))
                #account for a pointer for each element's motion + pointer
                if mobile_flag:
                    data_offset+= num_of_elems*12
                    weird_pointer += num_of_elems*8
                else:
                    data_offset+= num_of_elems*8
                    weird_pointer += num_of_elems*8
        
        #Animation names
        for anim in json_data["Animations"]:
            padded_name = padString(anim["Name"])
            f.write(bytes(padded_name, "shift-jis").replace(b' ', b'\x00'))
        
        #Elements!!!
        for bank in json_data["Element Banks"]:
            for element in bank:
                f.write(packInt(element["Unknown Flag 0"],4))
                f.write(packInt(element["Render Flag"],4))
                f.write(packInt(element["Unknown Flag 1"],4))
                for i in element["2D Polygon"]:
                    f.write(packFloat(i))
                f.write(packInt(element["Unknown Values"][0],4))
                pointer_list.append(f.tell())
                f.write(packPointer(data_offset+len(element["Sprite List"])*4))
                f.write(packInt(element["Unknown Values"][1],4))
                if endianness == "<":
                    f.write(struct.pack("<B", element["Render Settings"]["dodge_blend"]))
                    f.write(struct.pack("<B", element["Render Settings"]["unknown_1"]))
                    f.write(struct.pack("<B", element["Render Settings"]["unknown_2"]))
                    f.write(struct.pack("<B", 0))
                if endianness == ">":
                    f.write(struct.pack("<B", 0))
                    f.write(struct.pack("<B", element["Render Settings"]["unknown_2"]))
                    f.write(struct.pack("<B", element["Render Settings"]["unknown_1"]))
                    f.write(struct.pack("<B", element["Render Settings"]["dodge_blend"]))
                f.write(packInt(len(element["Sprite List"]), 4))
                
                pointer_list.append(f.tell())
                f.write(packPointer(data_offset))
                f.write(packInt(element["Unknown Values"][2],4))
                f.write(packPointer(0)) #???
                f.write(packPointer(0)) #???
                weird_pointer += 60
                data_offset+= 60
                weird_pointer += len(element["Sprite List"])*4
                data_offset+= len(element["Sprite List"])*4
        
        #Motion + offset
        for anim in json_data["Animations"]:
            for bank in anim["Element Banks"]:
                for element in bank:
                    #I would like to set the correct order of the motions first before moving on
                    element["Animations"] = sorted(element["Animations"], key=sortMotion)
                    motion_int = 0
                    motions = []
                    for motion in element["Animations"]:
                        motion_int += int(motion_names[motion["Motion"]])
                    #log(motion_int)
                    
                    f.write(packInt(motion_int,4))
                    if len(element["Animations"]) != 0:
                        pointer_list.append(f.tell())
                        f.write(packPointer(data_offset))
                        if mobile_flag:
                            data_offset+= len(element["Animations"])*16
                            weird_pointer += len(element["Animations"])*12
                        else:
                            data_offset+= len(element["Animations"])*12
                            weird_pointer += len(element["Animations"])*12
                    else:
                        f.write(packPointer(0))
        
        #Element sprite list + settings
        for bank in json_data["Element Banks"]:
            for element in bank:
                for sprite in element["Sprite List"]:
                    f.write(packInt(sprite, 4))
                
                #Settings
                f.write(packInt(element["Default Settings"]["hide"], 4))
                f.write(packFloat(element["Default Settings"]["posx"]))
                f.write(packFloat(element["Default Settings"]["posy"]))
                f.write(packFloat(element["Default Settings"]["angle"]))
                f.write(packFloat(element["Default Settings"]["scalex"]))
                f.write(packFloat(element["Default Settings"]["scaley"]))
                f.write(packFloat(element["Default Settings"]["sprite_index"]))
                packRGBA(element["Default Settings"]["rgba"], f)
                packRGBA(element["Default Settings"]["rgba_tl"], f)
                packRGBA(element["Default Settings"]["rgba_bl"], f)
                packRGBA(element["Default Settings"]["rgba_tr"], f)
                packRGBA(element["Default Settings"]["rgba_br"], f)
                
                # element_settings["audio_cue?"] = bytesToInt(elem_settings_off, 4)
                # elem_settings_off +=4
                
                # element_settings["3d_depth"] = bytesToInt(elem_settings_off, 4)
                # elem_settings_off +=4
                
                # element_settings["unk_motion"] = bytesToInt(elem_settings_off, 4)
                # elem_settings_off +=4
                
                f.write(packInt(element["Default Settings"]["audio_cue?"], 4))
                f.write(packInt(element["Default Settings"]["3d_depth"], 4))
                f.write(packInt(element["Default Settings"]["unk_motion"], 4))
        
        #Keyframes pointers!!
        for anim in json_data["Animations"]:
            for bank in anim["Element Banks"]:
                for element in bank:
                    for motion in element["Animations"]:
                        f.write(packInt(motion["Loop"],4))
                        f.write(packInt(len(motion["Keyframes"]),4))
                        pointer_list.append(f.tell())
                        f.write(packPointer(data_offset))
                        data_offset += len(motion["Keyframes"])*24
                        weird_pointer += len(motion["Keyframes"])*24
        
        #keyframes themselves and i'm basically done
        for anim in json_data["Animations"]:
            for bank in anim["Element Banks"]:
                for element in bank:
                    for motion in element["Animations"]:
                        for keyframe in motion["Keyframes"]:
                            f.write(packInt(keyframe["timestamp"], 4))
                            if motion["Motion"].find("rgba") != -1:
                                packRGBA(keyframe["data"], f)
                            elif motion["Motion"].find("hide") != -1 or motion["Motion"].find("3d_depth") != -1 or motion["Motion"].find("audio_cue?") != -1 or motion["Motion"].find("unk_motion") != -1:
                                f.write(packInt(keyframe["data"], 4))
                            else:
                                f.write(packFloat(keyframe["data"]))
                            f.write(packInt(keyframe["tweening"], 4))
                            f.write(packFloat(keyframe["ease_in"]))
                            f.write(packFloat(keyframe["ease_out"]))
                            f.write(packFloat(keyframe["unk"]))
        current_offset = f.tell()
        f.seek(4)
        f.write(packInt(current_offset-8,4, "<"))
        #add padding i guess
        while current_offset % 16 != 0:
            current_offset += 1
            weird_pointer += 1
            #print(current_offset)
        
        f.seek(current_offset)
        nof0_pointer = current_offset
        nof0_size = len(pointer_list)*4 + 12
        f.write(bytes("NOF0", 'UTF-8'))
        f.write(packInt(len(pointer_list)*4 + 12,4, "<"))
        f.write(packInt(len(pointer_list),4))
        f.write(packInt(0,4))
        for i in pointer_list:
            f.write(packInt(i,4))
        
        current_offset = f.tell()
        #add padding i guess
        while current_offset % 16 != 0:
            current_offset += 1
        f.seek(current_offset)
        f.write(bytes("NEND", 'UTF-8'))
        f.write(packInt(0,8))
        f.write(packInt(0,4))
        f.close()
    
    
    with open(output_file, "r+b") as f:
        animation_hex = f.read()
        f.close()
    
    with open(output_file, "wb") as f:
        f.write(bytes(json_data["Misc. Info"]["Header Magic"], 'UTF-8'))
        f.write(packInt(24, 4, "<"))
        f.write(packInt(1, 4))
        f.write(packInt(32, 4))
        if mobile_flag:
            f.write(packInt(weird_pointer, 4))
        else:
            f.write(packInt(weird_pointer, 4))
        f.write(packInt(nof0_pointer+32, 4))
        f.write(packInt(nof0_size+4, 4))
        f.write(packInt(1, 4))
        f.write(animation_hex)
    log("Pointer List:")
    log(pointer_list) 