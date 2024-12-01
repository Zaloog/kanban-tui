# VHS documentation
#
# Output:
#   Output <path>.gif               Create a GIF output at the given <path>
#   Output <path>.mp4               Create an MP4 output at the given <path>
#   Output <path>.webm              Create a WebM output at the given <path>
#
# Require:
#   Require <string>                Ensure a program is on the $PATH to proceed
#
# Settings:
#   Set FontSize <number>           Set the font size of the terminal
#   Set FontFamily <string>         Set the font family of the terminal
#   Set Height <number>             Set the height of the terminal
#   Set Width <number>              Set the width of the terminal
#   Set LetterSpacing <float>       Set the font letter spacing (tracking)
#   Set LineHeight <float>          Set the font line height
#   Set LoopOffset <float>%         Set the starting frame offset for the GIF loop
#   Set Theme <json|string>         Set the theme of the terminal
#   Set Padding <number>            Set the padding of the terminal
#   Set Framerate <number>          Set the framerate of the recording
#   Set PlaybackSpeed <float>       Set the playback speed of the recording
#   Set MarginFill <file|#000000>   Set the file or color the margin will be filled with.
#   Set Margin <number>             Set the size of the margin. Has no effect if MarginFill isn't set.
#   Set BorderRadius <number>       Set terminal border radius, in pixels.
#   Set WindowBar <string>          Set window bar type. (one of: Rings, RingsRight, Colorful, ColorfulRight)
#   Set WindowBarSize <number>      Set window bar size, in pixels. Default is 40.
#   Set TypingSpeed <time>          Set the typing speed of the terminal. Default is 50ms.
#
# Sleep:
#   Sleep <time>                    Sleep for a set amount of <time> in seconds
#
# Type:
#   Type[@<time>] "<characters>"    Type <characters> into the terminal with a
#                                   <time> delay between each character
#
# Keys:
#   Escape[@<time>] [number]        Press the Escape key
#   Backspace[@<time>] [number]     Press the Backspace key
#   Delete[@<time>] [number]        Press the Delete key
#   Insert[@<time>] [number]        Press the Insert key
#   Down[@<time>] [number]          Press the Down key
#   Enter[@<time>] [number]         Press the Enter key
#   Space[@<time>] [number]         Press the Space key
#   Tab[@<time>] [number]           Press the Tab key
#   Left[@<time>] [number]          Press the Left Arrow key
#   Right[@<time>] [number]         Press the Right Arrow key
#   Up[@<time>] [number]            Press the Up Arrow key
#   Down[@<time>] [number]          Press the Down Arrow key
#   PageUp[@<time>] [number]        Press the Page Up key
#   PageDown[@<time>] [number]      Press the Page Down key
#   Ctrl+<key>                      Press the Control key + <key> (e.g. Ctrl+C)
#
# Display:
#   Hide                            Hide the subsequent commands from the output
#   Show                            Show the subsequent commands in the output

Output demo.gif

Require ktui

Set Width 1600
Set Height 1200
Set Shell zsh

Sleep 1s
Type "ktui demo"
Sleep 1s
Enter
Escape
Type "[?2026;2$y"
Escape
Type "[?2048;2$y"
Sleep 2s
Type "j"
Sleep 1s
Type "j"
Sleep 500ms
Type "k"
Sleep 1.5s
Type "L"
Sleep 500ms
Type "L"
Sleep 1.5s
Escape
Type "[107;5u"
Sleep 1s
Type " "
Sleep 2s
Type " "
Sleep 2.5s
Escape
Type "[106;5u"
Sleep 1s
Type "B"
Sleep 1s
Type "j"
Sleep 500ms
Enter
Sleep 1s
Type "n"
Sleep 500ms
Type "New Task"
Sleep 500ms
Tab
Sleep 500ms
Type "- Markdown Support"
Sleep 2s
Tab
Sleep 1s
Tab
Sleep 500ms
Tab
Sleep 500ms
Enter
# Sleep 4.5s
# ctrlc exit
#Escape
#Type "[99;5u"
#Ctrl+D
# End
Escape
Type "[108;5u"
Sleep 1s
Tab 8
Sleep 500ms
Type "j"
Sleep 500ms
Type "j"
Sleep 1.5s
Type "n"
Sleep 500ms
Type "New"
Type "Column"
Sleep 500ms
Tab
Enter
Sleep 1s
Escape
Type "[106;5u"
Sleep 2s
Escape
Type "[99;5u"
Ctrl+D
