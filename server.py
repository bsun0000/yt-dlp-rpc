import os
import sys
import io
import json
import re
import ssl
import urllib.parse
import logging
import asyncio
from contextlib import redirect_stdout
from datetime import datetime

import aiohttp
from aiohttp import web

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Log Python environment information
logger.info(f"Python version: {sys.version}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Initial sys.path: {sys.path}")

# Modify Python path
script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)
logger.info(f"Added to sys.path: {parent_dir}")
logger.info(f"Updated sys.path: {sys.path}")

# Now import yt_dlp after modifying the path
try:
    import yt_dlp
    logger.info(f"yt_dlp successfully imported from: {yt_dlp.__file__}")
except ImportError as e:
    logger.error(f"Error importing yt_dlp: {e}")
    logger.info("Attempting to locate yt_dlp manually...")
    for path in sys.path:
        potential_path = os.path.join(path, 'yt_dlp')
        if os.path.exists(potential_path):
            logger.info(f"yt_dlp directory found at: {potential_path}")
        else:
            logger.info(f"yt_dlp not found in: {potential_path}")
    sys.exit(1)
    
#import cProfile
#import pstats

ip_server = '127.0.0.1'
port_number = 9120

def decode_unicode_escapes(text):
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)

async def get_video_info(url, user_agent="Mozilla/5.0 (iPad; CPU OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 SP-engine/2.69.0 main/1.0 baiduboxapp/13.31.0.10 (Baidu; P2 17.5.1) NABar/1.0"):
    headers = {
        'User-Agent': user_agent,
        'Connection': 'close'
    }
    
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=ssl_context, timeout=3) as response:
                html = await response.text()

        title_match = re.search(r'"title":"(.*?)"', html)
        length_match = re.search(r'"lengthSeconds":"(\d+)"', html)

        title = "No title found"
        length_seconds = 0

        if title_match:
            title = title_match.group(1)
            title = decode_unicode_escapes(title)
        if length_match:
            length_seconds = int(length_match.group(1))

        result = {
            "title": title,
            "duration": length_seconds
        }
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        return ""

async def invoke_ytdlp(request_argv):
    #profiler = cProfile.Profile()
    #profiler.enable()
    ret = b''
    try:
        loop = asyncio.get_running_loop()
        with io.StringIO() as buf, redirect_stdout(buf):
            await loop.run_in_executor(None, yt_dlp._real_main, request_argv)
            buf.seek(0)
            buf2 = io.BytesIO(buf.read().encode('utf8'))
            ret = buf2.getvalue()
    except Exception as e:
        logger.error(f"Error in invoke_ytdlp: {str(e)}")
        
    #profiler.disable()
    #stats = pstats.Stats(profiler).sort_stats('cumulative')
    #stats.print_stats()
    return ret

async def handler(request):
    start_time = datetime.now()
    logger.info(f"Received {request.method} request from {request.remote}")

    try:
        if request.method == "GET":
            params = request.query

            if 'url' not in params:
                logger.warning("Bad request: Missing url parameter")
                return web.Response(text='403 Bad Request: Missing url parameter', status=403)
            url = urllib.parse.unquote(params['url'])
            logger.info(f"Processing URL: {url}")

            if 'get_title' in params:
                info = await get_video_info(url)
                if info:
                    logger.info("Successfully retrieved video info")
                    return web.Response(text=info, content_type='text/plain')
                    
            if 'get_player' in params:
                request_argv = [
                    "--no-warnings", "-J", "--extractor-args", "youtube:player_client=ios",
                    "--flat-playlist", "--cookies", script_dir + "/cookies.txt", "--no-check-certificate",
                    "--format", "bestvideo[width<=1920][vcodec!~='vp0?9'][vcodec!~='av1?9'][protocol^=https]+bestaudio[protocol^=https]/bestvideo[width<=1920][vcodec!~='vp0?9'][vcodec!~='av1?9']+bestaudio/best",
                    "--", url
                ]

                result = await invoke_ytdlp(request_argv)
                if result:
                    logger.info("Successfully retrieved player info")
                    return web.Response(body=result, content_type='text/plain')

            logger.warning("Request processing failed")
            return web.Response(text='500 Something went wrong or bad request was made', status=500)

        elif request.method == "POST":
            request_body = await request.read()
            request_argv = [param.decode('utf-8') for param in request_body.splitlines()]
            logger.info(f"Processing POST request with arguments: {request_argv}")

            result = await invoke_ytdlp(request_argv)
            if result:
                logger.info("Successfully processed POST request")
                return web.Response(body=result, content_type='text/plain')

        logger.warning("Request processing failed")
        return web.Response(text='500 Something went wrong or bad request was made', status=500)

    except Exception as e:
        logger.error(f"Unhandled exception in handler: {str(e)}")
        return web.Response(text='500 Internal Server Error', status=500)

    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Request processed in {duration:.2f} seconds")

async def site_dispatch(request):
    if request.remote == ip_server:
        return await handler(request)
    logger.warning(f"Forbidden access attempt from {request.remote}")
    return web.Response(text='403 Forbidden', status=403)

if __name__ == '__main__':
    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', site_dispatch)
    
    logger.info(f'Starting httpserver at http://{ip_server}:{port_number}/')
    web.run_app(app, host=ip_server, port=port_number, access_log=logger)
