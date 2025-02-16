# discord-compressor
A simple program that compresses any regular video down to fit within Discord's 10MiB upload limit while maximizing quality.

# Current dependencies
Current dependencies are:
* FFmpeg
* Python

# How to use
* Open a terminal inside the same directory as the program code and run ``python main.py <input.mp4>``
Where <input.mp4> is the file path of the video you want to compress (drag and drop into the Windows terminal).
* If the program detects a low enough bitrate bandwidth, you might be asked if you want to drop the audio. Doing so will dedicate more bandwidth to the video portion.
* Next you will have to provide a number for how fast you want the program to run, from 0 to 9.
  * Each number selects a corresponding x265 preset value, from "placebo" (0) to "ultrafast" (9).
  * Each step down in speed will make the program run for significantly longer, while the quality improvements become less and less noticable.
  * For a solid and quick compression, preset 7 ("veryfast") is highly recommended. If you're looking to maximize quality, try 3 ("slow")
  * Unless you're in the future, I wouldn't recommend going lower than 3, as the encode times at the lowest speeds can take up to an hour on slower computers.
* Once the program has finished running, a video titled "compressed.mp4" will appear in the program directory. This is the finished product after compression, and should be below 10 MiB.
  * Move the file, rename it, and or just upload it to Discord and delete the local copy afterwards! :D

# Warning
If you don't move or rename the output file, it will be overwritten next time the program runs!

# Report mistakes and errors!
If you think you have found and error/bug or something else is bothering you about the program, feel free to reach out or open an issue! (If opening issues is possible, I'm still new to github)


