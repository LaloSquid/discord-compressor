import subprocess
import ffmpeg
import sys
from math import sqrt

file_size_limit = 10 #File size limit in MiB

def determine_audio_channels(bandwidth:int, probe_info) -> int:
    """
    Ask the user how many audio channels will be exported.
    From 0 to 2.
    """
    audio_streams = [stream for stream in probe_info["streams"] if stream["codec_type"] == "audio"]
    if audio_streams:
        source_audio_channels = audio_streams[0]["channels"]
        print(f"Found {source_audio_channels} audio channels.")
    else:
        source_audio_channels = 0
        print("No audio channels were found.")

    if source_audio_channels >= 1:
        if bandwidth >= 386_000 and source_audio_channels >= 2:
            #If there is sufficient bandwidth, and enough source audio channels, output will be stereo
            audio_channels = 2 
        elif bandwidth < 192_000:
            print(f"Total bit bandwitdh is extremely low of {bandwidth}bps. Consider dropping the audio all together, which will provide more bandwidth to the video stream. Do you want to drop the audio? (y/n)")
            answer = str(input())
            while answer != "y" and answer != "n":
                answer = str(input("Please provide a valid response.\n"))
            if answer == "y":
                audio_channels = 0
            elif answer == "n":
                audio_channels = 1
        else:
            #If not, audio will be mono
            audio_channels = 1
    else:
        audio_channels = 0
    return audio_channels
  

def calculate_total_bandwidth(duration:float,file_size_limit:int) -> int:
    """
    Given duration and file size limits, calculates the total bandwidth for this operation.
    This does not yet consider what bitrate is dedicated to audio/video.
    """
    bitrate_bandwidth = int((1_048_576 * 8 * file_size_limit)/duration)
    return bitrate_bandwidth


def calculate_video_bitrate(bandwidth:int,audio_channels:int) -> int:
    """
    Given the total bandwidth, and number of chosen audio channels, this function calculates
    how much bitrate will be dedicated to the video portion of the media.
    """
    video_bitrate = bandwidth - audio_channels * 32000 #For each audio channel, 32kbps is taken away from the video stream. Later to be given to audio.
    video_bitrate = video_bitrate - 13000 #Takes away 13kbps just to make sure the stream will fit inside the file size limit.
    if video_bitrate < 0:
        video_bitrate = 0
    return video_bitrate


def _round_to_even(n):
    rounded = round(n)
    if rounded % 2 != 0:
        if n > rounded:
            rounded = rounded + 1
        else:
            rounded = rounded - 1
    return rounded


def calculate_video_resolution(source_width:int, source_height:int, video_bitrate:int) -> tuple:
    """
    """
    aspect_ratio = source_width / source_height
    bits_per_pixel = 2 #I found 2 to be a good value
    calculated_height = sqrt(video_bitrate/(bits_per_pixel * aspect_ratio))
    if calculated_height > source_height:
        calculated_height = source_height
    output_height = _round_to_even(calculated_height)
    output_width = _round_to_even(calculated_height * aspect_ratio)
    return (output_width, output_height)


def ask_preset() -> str:
    """
    Asks for the encoding preset speed
    """
    presets = [
        "placebo", "veryslow", "slower", "slow", "medium",
        "fast", "faster", "veryfast", "superfast", "ultrafast"
    ]
    print("------------------------------------------")
    print("From 0 to 9, How fast do you want the program to run?\nSlower speeds = higher quality, with deminishing returns for every slower speed.\nI don't recommend going below 5 unless you are in the future or have a super fast cpu.")
    while True:
        try:
            entered_number = int(input())
            if entered_number < 0 or entered_number > 9:
                print("Invalid input. Please enter an integer from 0 to 9")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter an integer from 0 to 9")
    return presets[entered_number]


def get_frame_rate(probe_info) -> float:
    frame_rate = probe_info["streams"][0]["r_frame_rate"]
    numerator, denominator = map(int, frame_rate.split("/"))
    output_frame_rate = numerator / denominator
    if output_frame_rate > 60:
        output_frame_rate = 60
    return float(output_frame_rate)


def encode_job(video_path:str, video_bitrate:int, audio_bitrate:int, preset:str, frame_rate:int, resolution:tuple, audio_channels:int) -> None:
    """
    Does the encoding
    """
    if audio_channels == 0:
        audio_command_list = ["-an"]
    else:
        audio_command_list = ["-c:a", "libopus", "-ac", str(audio_channels), "-b:a", str(audio_bitrate), "-vbr", "off"]

    #First pass, no audio, no watchable video
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-c:v", "libx265",
        "-tag:v", "hvc1", 
        "-an", 
        "-pix_fmt", "yuv420p", "-b:v", str(video_bitrate), 
        "-preset", preset, "-r", str(frame_rate), "-g", str(frame_rate * 10), 
        "-s", str(resolution[0])+"x"+str(resolution[1]), 
        "-x265-params", "pass=1", "-f", "null", "-"
        ])

    #Second pass, audio and file creation
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-c:v", "libx265", 
        "-tag:v", "hvc1", 
        *audio_command_list, 
        "-pix_fmt", "yuv420p", "-b:v", str(video_bitrate), 
        "-preset", preset, "-r", str(frame_rate), "-g", str(frame_rate * 10), 
        "-s", str(resolution[0])+"x"+str(resolution[1]), 
        "-x265-params", "pass=2", "compressed.mp4"
        ])


if len(sys.argv) < 2:
    print("Usage: python main.py <video_file>")
    sys.exit(1)
video_path = sys.argv[1]
probe_info = ffmpeg.probe(video_path)
print(probe_info)
duration = float(probe_info["format"]["duration"])
print(f"Given video duration: {duration:.3f}s")
bandwidth = calculate_total_bandwidth(duration,file_size_limit)
print(f"Total media bandwidth: {bandwidth}bps")
audio_channels = determine_audio_channels(bandwidth,probe_info)
video_bitrate = calculate_video_bitrate(bandwidth,audio_channels)
audio_bitrate = audio_channels * 32000
print(f"Video bitrate: {video_bitrate}bps\nAudio bitrate: {audio_bitrate}bps")
source_width = int(probe_info["streams"][0]["width"])
source_height = int(probe_info["streams"][0]["height"])
output_resolution = calculate_video_resolution(source_width,source_height,video_bitrate)
print(f"The output resolution has been set to {output_resolution[0]}x{output_resolution[1]}")
preset = ask_preset()
frame_rate = get_frame_rate(probe_info)
print(f"Detected framerate: {frame_rate}")
encode_job(video_path, video_bitrate, audio_bitrate, preset, frame_rate, output_resolution, audio_channels)