import subprocess
import sys

def get_video_duration(filepath:str):
    """
    Returns the video length in seconds, as a float, of a given filepath to a video.
    """
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filepath],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    return float(result.stdout)

if len(sys.argv) < 2:
    print("Usage: python main.py <video_file>")
    sys.exit(1)

video_path = sys.argv[1]
duration = get_video_duration(video_path)

if duration is not None:
    print(f"Video duration: {duration:.2f} seconds.")