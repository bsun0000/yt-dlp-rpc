# yt-dlp-rpc
(yt-dlp) Proof-of-concept RPC server implementation

This is an example server program (written in Python) implementing basic RPC logic for the yt-dlp program.

The goal is to keep yt-dlp loaded in memory, cutting away any overheads and delays coming from a Python interpreter and disk I/O.

Requires the `aiohttp` Python library to be installed, in addition to all yt-dlp dependencies (except optional ones).

## How to use:

1. Clone the yt-dlp repository
2. Place `server.py` in the `yt-dlp/yt_dlp` folder
3. Run `server.py`

By default, it binds to:
```
ip_server = '127.0.0.1'
port_number = 9120
```

The server waits for POST requests containing yt-dlp parameters.

## Additional Usage Examples

The server handles two GET requests:

### Get the video title and duration:
```
/?get_title=1&url=<youtube_url>
```
- URL must be URL-encoded
- Fetches the URL, looking for the title and duration variables. Implemented in a dumb way - without using yt-dlp
- The result is a text response containing a JSON array with "title" and "duration" values

### Get player information:
```
/?get_player=1&url=<youtube_url>
```
- Invokes the yt-dlp module, requesting video information in JSON format (-J)
- This is an example, all options are hardcoded inside server.py itself.

## yt-dlp-rpc.cpp

Contains an example program to interface with this server. It takes normal command-line options (as if you were calling yt-dlp directly), passes them to the server, and returns the result.
Obviosly, interactive functionality will not be available here. Not even the progress bar.
It can be used as a standalone program or in combination with the MPV player:

Add to your `mpv.conf` file:
```
script-opts=ytdl_hook-ytdl_path=<path to the rpc-client program>
```

Tested both on Windows and Linux.

## SECURITY NOTICE!

**This server does not have any built-in security features!**

- It does not filter the input by any means
- It allows all yt-dlp flags to be used
- This POC is a potential security vector that can allow malicious actors to do harmful things to your system

**USE AT YOUR OWN RISK!**
