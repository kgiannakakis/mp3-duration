# mp3-duration
Port of [node.js mp3-duration](https://github.com/ddsol/mp3-duration) to Python 2.6+

# Usage

```python
import mp3_duration

# Get duration in milli-seconds
duration_ms = mp3_duration(filename)

# Estimate duration (faster, but inaccurate results)
duration_ms = mp3_duration(filename, True)
```

You can also run the tool from command line:

```Shell
python mp3_duration path_to_mp3_file
python mp3_duration -e path_to_mp3_file
```
