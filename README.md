# Puyo Puyo Animation Converter
Puyo Puyo animation converter to Json format and back.
This script was made in python 3.4.

Correct usage: `puyo_anim.py [input file] [options]`

Available options:        
`-o` Output file. This will be determined automatically if not set.  
`-ds` Converting to or from a Nintendo DS animation file.        
`-3ds` Converting to or from a Nintendo 3DS animation file.        
`-m` Converting to or from a mobile file. This includes Puyo Puyo Quest and Puyo Puyo Touch.  
`--name_order` Keep the order of the elements.                      
Some animation files have an oddly specific order for it's names that the games can be hardcoded to expect.                      
Recommended if you're editing UI or Manzai animations, but not for general animation editing, like cut-ins.

`-dbg` | `--debug` Enable printing debug info

Example:        
  `puyo_anim.py title.snc -o title.snc.json`        Converts from a binary animation file to a .json.  
  `puyo_anim.py title.snc.json -o title.snc`        Converts from a .json file to a binary.
  
The conversion will depend on the file extension of the input.If the extension is '.json', then it will convert the json to it's corresponding animation file format.
If it has any extension other than 'json', or no extension at all, it will treat the input file as an animation file.

# Formats Supported 
These are the common extensions you'll find that are supported.  
`.snc` - Playstation 2 / Playstation Portable  
`.dncs` - Nintendo DS / Nintendo 3DS / Android & iOS  
`.gncs` - Wii  
  
In some cases, such as Puyo Puyo Quest, the animation files will have no extension and you'll have to identify them manually.
