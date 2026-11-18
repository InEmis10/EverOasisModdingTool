## Ever Oasis Modding tool

Objective : 
Add new content to Ever Oasis by making a tool like Kuriimu but for Ever Oasis.

Libs:
- Pygame -> to core window
- Py Game Easy Gui -> a lib of my own to make Gui

Features:
- Pack and Unpack .gar file (sub archive storing model , shaders, map , collision map ect ...) , the project can UnPack and Pack but i don't test in game so its not 100% sure its working.
- "Decompile" script, script from Ever Oasis are pretty simple to decompile because its compiled with Squirrel.
- Project tree -> View all the file opened into a folder
- Workspace set up -> make a project set - up to when you finish your game modification you juste have to use tool->Build to "build" the mods
- Read .dbd format

TODO:
- Make the build features
- Add mods folder path to settings to build and move directly to the game mods folder
- Add citra Launch from the tool (TODO but not sure : Try to launch citra with modified file into the workspace directly to make testing really fast, 2-Make compatibility with others emluator)
- Audio listening for audio file
- Texture / Image view
- Save and edit Scripts (TODO bis: code completion ? Debugger? Lint?)
- Save and edit .dbd data table

IDEA:
- Engin Hook? + add libc opcode to Engine's Squirrel compilator ? (really hard for me i not gonna lie)
- Implement libc ? (why : code execution like write() , read() , printf()
- Redirect all print from scripts into stdout ? (attach cmd prompt subproc?)

TARGET MODS TYPE:
- Add npc
- Add weapon
- Stat modification
- Expand Oasis max level (already possible in theory)
  
