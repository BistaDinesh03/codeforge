"""
Server Discovery via mDNS (Bonjour/Avahi).
Allows VS Code extension to find the server automatically on the local network.
"""

import socket
import threading
import time
from typing import Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Service type for mDNS
SERVICE_TYPE = "_codeforge._tcp.local."
SERVICE_NAME = f"CodeForge-{socket.gethostname()}._codeforge._tcp.local."


class DiscoveryService:
    """
    Advertises the CodeForge server on the local network using mDNS.
    Works on Windows, Linux, and macOS.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._host = settings.HOST
        self._port = settings.PORT

    def start(self) -> None:
        """Start advertising the server on the network."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Discovery service started on port {self._port}")

    def stop(self) -> None:
        """Stop advertising."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Discovery service stopped")

    def _run(self) -> None:
        """
        Simple UDP broadcast for discovery.
        
        Every 30 seconds, broadcasts a JSON packet on the local network.
        Extensions listen for these packets to find the server.
        
        This is a simplified version of mDNS that works without
        additional dependencies on all platforms.
        """
        broadcast_port = 45678  # Fixed port for discovery
        
        while self._running:
            try:
                # Create UDP socket for broadcasting
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(2)
                
                # Get actual IP address
                local_ip = self._get_local_ip()
                
                # Build discovery message
                message = (
                    f'{{"service":"codeforge","host":"{local_ip}",'
                    f'"port":{self._port},"version":"{settings.APP_VERSION}",'
                    f'"name":"{socket.gethostname()}"}}'
                )
                
                # Broadcast to all devices on the subnet
                sock.sendto(message.encode(), ('<broadcast>', broadcast_port))
                logger.debug(f"Discovery broadcast sent: {message}")
                
                sock.close()
                
            except Exception as e:
                logger.debug(f"Discovery broadcast failed: {e}")
            
            # Wait before next broadcast
            for _ in range(30):
                if not self._running:
                    break
                time.sleep(1)

    def _get_local_ip(self) -> str:
        """Get the local network IP address."""
        try:
            # Connect to a dummy address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


# Singleton
_discovery_service: Optional[DiscoveryService] = None


def get_discovery_service() -> DiscoveryService:
    """Get or create the discovery service singleton."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service