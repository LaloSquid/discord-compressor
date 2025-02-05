import subprocess

def get_length(filename:str):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    return float(result.stdout)

print(get_length("streamer.webm"))