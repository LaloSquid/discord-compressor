import subprocess
import sys
from math import ceil

file_size_limit = 10 #File size limit in MB

def ask_audio_channels() -> int:
    """
    Ask the user how many audio channels will be exported.
    From 0 to 2.
    """
    print("How many audio channels?\n0 = no audio, 1 = mono, 2 = stereo.\nFewer audio channels means more bitrate for the video.")
    while True:
        try:
            entered_number = int(input())
            while entered_number < 0 or entered_number > 2:
                entered_number = int(input("Given number fell outside of the range (0, 1 or 2), please try again.\n"))
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")
    return entered_number


def calculate_total_bandwidth(duration:float,file_size_limit:int) -> float:
    """
    Given duration and file size limits, calculates the total bandwidth for this operation.
    This does not yet consider what bitrate is dedicated to audio/video.
    """
    bitrate_bandwidth = 1000 * ((file_size_limit * 8)/duration)
    return bitrate_bandwidth

def get_video_duration(filepath:str) -> float:
    """
    Returns the video length in seconds, as a float, of a given filepath to a video.
    """
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filepath],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    return float(result.stdout)

def get_video_resolution(filepath:str) -> tuple:
    """
    Returns the video resolution as a tuple like (1920,1080)
    """
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "stream=width,height", "-of",
                             "default=noprint_wrappers=1:nokey=1", filepath],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    result = result.stdout
    resolution = tuple(map(int, result.decode().split()))
    return resolution

def get_video_aspect_ratio(video_resolution:tuple) -> float:
    """
    Returns the aspect ratio of a video based on its resolution, in a float format.
    For example 1920x1080, which is 16:9, will return as 1.777777...
    """
    ratio = video_resolution[0] / video_resolution[1]
    return ratio

def calculate_video_bitrate(bandwidth:float,audio_channels:int) -> int:
    """
    Given the total bandwidth, and number of chosen audio channels, this function calculates
    how much bitrate will be dedicated to the video portion of the media.
    """
    video_bitrate = bandwidth - audio_channels * 32 #For each audio channel, 32kbps is taken away from the video stream. Later to be given to audio.
    video_bitrate = video_bitrate - 10 #Takes away 10kbps just to make sure the stream will fit inside the file size limit.
    if video_bitrate < 0:
        video_bitrate = 0
    return int(video_bitrate)

def get_source_frame_rate(filepath:str) -> float:
    """
    Extracts the framerate as a float, using ffprobe.
    """
    result = subprocess.run(["ffprobe", "-v", "error", 
                             "-select_streams", "v:0",
                             "-show_entries", "stream=r_frame_rate", 
                             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    result = result.stdout
    numerator, denominator = map(int, result.decode().split('/'))  # Works fine
    fps = numerator / denominator
    return fps

def ask_frame_rate(source_frame_rate:float) -> int:
    """
    Asks for the desired framerate
    """
    print("Enter the desired framerate. A lower one can improve image quality.")
    while True:
        try:
            entered_number = int(input())
            if entered_number < 1 or entered_number > source_frame_rate:
                print("Invalid input. Please enter a positive integer, no larger than source framerate.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
    return entered_number

def ask_preset() -> str:
    """
    Asks for the encoding preset speed
    """
    presets = [
        "placebo", "veryslow", "slower", "slow", "medium",
        "fast", "faster", "veryfast", "superfast", "ultrafast"
    ]
    print("From 1 to 10, How fast do you want the program to run?\nSlower speeds = higher quality, but each step down results in deminishing returns.\nI don't recommend going below 4 unless you are in the future or have a super fast cpu.")
    while True:
        try:
            entered_number = int(input())
            if entered_number < 1 or entered_number > 10:
                print("Invalid input. Please enter an integer from 1 to 10")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter an integer from 1 to 10")
    return presets[entered_number - 1]

def encode_job(video_path:str, video_bitrate:int, audio_bitrate:int, preset:str, frame_rate:int, resolution:tuple, audio_channels:int) -> None:
    """
    Does the encoding
    """
    #First pass, no audio, no watchable video
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-c:v", "libx265", 
        "-an", 
        "-pix_fmt", "yuv420p", "-b:v", str(video_bitrate)+"k", 
        "-preset", preset, "-r", str(frame_rate), "-g", str(frame_rate * 10), 
        "-s", str(resolution[0])+"x"+str(resolution[1]), 
        "-x265-params", "pass=1", "-f", "null", "-"
        ])

    #Second pass, audio and file creation
    if audio_channels == 0:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-c:v", "libx265", 
            "-an", 
            "-pix_fmt", "yuv420p", "-b:v", str(video_bitrate)+"k", 
            "-preset", preset, "-r", str(frame_rate), "-g", str(frame_rate * 10), 
            "-s", str(resolution[0])+"x"+str(resolution[1]), 
            "-x265-params", "pass=2", "compressed.mp4"
            ])
    else:    
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-c:v", "libx265", 
            "-c:a", "libopus", "-ac", str(audio_channels), "-b:a", str(audio_bitrate)+"k", 
            "-pix_fmt", "yuv420p", "-b:v", str(video_bitrate)+"k", 
            "-preset", preset, "-r", str(frame_rate), "-g", str(frame_rate * 10), 
            "-s", str(resolution[0])+"x"+str(resolution[1]), 
            "-x265-params", "pass=2", "compressed.mp4"
            ])

if len(sys.argv) < 2:
    print("Usage: python main.py <video_file>")
    sys.exit(1)
video_path = sys.argv[1]
duration = get_video_duration(video_path)
print(f"Given video duration: {duration:.3f}s")
bandwidth = calculate_total_bandwidth(duration,file_size_limit)
print(f"Total media bandwidth: {bandwidth:.2f}kbps")
if bandwidth < 64:
    print("Just give up bro. The bandwitdh is so low that the video will be unwatchable.")
elif bandwidth < 160:
    print("Due the total bandwitdh being less than 160kbps, I recommend leaving audio out entirely.")
elif bandwidth < 192:
    print("Due the total bandwitdh being less than 192kbps, I recommend at most only using mono audio.")
audio_channels = ask_audio_channels()
video_bitrate = calculate_video_bitrate(bandwidth,audio_channels)
audio_bitrate = audio_channels * 32
print(f"Video bitrate: {video_bitrate}kbps\nAudio bitrate: {audio_bitrate}kbps")
source_resolution = get_video_resolution(video_path)
video_aspect_ratio = get_video_aspect_ratio(source_resolution)
given_video_height = 0
while given_video_height < 1:
    given_video_height = int(input("What should the resolution of the video be? Only provide height, like 720 for 1280x720\n"))
if given_video_height > source_resolution[1]:
    print(f"Provided video height of {given_video_height} is larger than source height of {source_resolution[1]}, using source resolution of {source_resolution[0]}x{source_resolution[1]} instead.")
    output_resolution = source_resolution
else:
    output_resolution = (int(ceil(given_video_height * video_aspect_ratio)),given_video_height)
    print(f"The output resolution has been set to {output_resolution[0]}x{output_resolution[1]}")
source_frame_rate = get_source_frame_rate(video_path)
output_frame_rate = ask_frame_rate(source_frame_rate)
preset = ask_preset()
encode_job(video_path, video_bitrate, audio_bitrate, preset, output_frame_rate, output_resolution, audio_channels)