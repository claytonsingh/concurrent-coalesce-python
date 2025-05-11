from aiohttp import web
import asyncio
import subprocess
import ipaddress
from concurrent_coalesce import coalesce

def is_valid_ip(ip_str: str) -> bool:
    """Validate if the string is a valid IP address."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

@coalesce()
async def ping_host(host: str) -> dict:
    """Execute ping command for the given host and return results asynchronously."""
    print("Collecting data for host: ", host)

    # -n 4 for Windows (4 packets), -c 4 for Unix-like systems
    ping_args = ['ping', '-n', '4', host] if subprocess.sys.platform == 'win32' else ['ping', '-c', '4', host]
    
    # Use asyncio.create_subprocess_exec for true asynchronous subprocess execution
    process = await asyncio.create_subprocess_exec(
        ping_args[0], *ping_args[1:],
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, text=True
    )
    
    # Wait for the process to complete and get output
    stdout, stderr = await process.communicate()
    
    return {
        'host': host,
        'success': process.returncode == 0,
        'output': stdout,
        'error': stderr if stderr else None
    }

async def handle_ping(request: web.Request) -> web.Response:
    """Handle ping requests."""
    # Get host parameter
    host = request.query.get('host')
    if not host:
        return web.json_response(
            {'error': "Missing 'host' parameter"},
            status=400
        )
    
    # Validate that host is an IP address
    if not is_valid_ip(host):
        return web.json_response(
            {'error': "Host must be a valid IP address (IPv4 or IPv6)"},
            status=400
        )
    
    try:
        # Execute ping using coalesced function
        response = await ping_host(host)
        return web.json_response(response)
    except Exception as e:
        return web.json_response(
            {'error': str(e)},
            status=500
        )

if __name__ == "__main__":
    """Start the async web server."""
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    print("Server running on port 8000")
    print("Try accessing: http://localhost:8000/?host=8.8.8.8")
    web.run_app(app, host='localhost', port=8000)
