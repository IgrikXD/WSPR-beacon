from beaconapp.transports.base_transport import BaseTransport
from beaconapp.data_wrappers import Transport
from colorama import Fore, Style
from typing import Optional
from websockets.asyncio.client import connect as ws_connect, ClientConnection
from websockets.exceptions import ConnectionClosed

import asyncio
import json
import logging
import socket


logger = logging.getLogger(__name__)


class WebsocketTransport(BaseTransport):
    """
    WebSocket (Wi-Fi) transport implementation using asyncio and websockets library.
    """
    def __init__(self, device, hostname: str, port: int):
        super().__init__(device)
        self._websocket: Optional[ClientConnection] = None
        self._hostname = hostname
        self._port = port

        self._connect_timeout = 10.0
        self._close_timeout = 1.0
        self._reconnect_delay = 1.0

    async def connect(self):
        """
        Continuously tries to connect to the WebSocket with manual reconnection loop.
        Uses explicit connection management for proper control over connection lifecycle.
        """
        while not self._device.is_stop_flag_set():
            try:
                self._websocket = await asyncio.wait_for(
                    ws_connect(
                        uri=f"ws://{self._hostname}:{self._port}",
                        close_timeout=self._close_timeout,
                    ),
                    timeout=self._connect_timeout
                )
                # Notify about new available transport
                self._device.on_transport_connected(Transport.WIFI)

                # Immediately request device info upon successful connection
                self._device.get_device_info()

                # Receive messages until connection is closed or cancelled
                await self._websocket_receiver(self._websocket)

            except (OSError, socket.gaierror, TimeoutError):
                # Expected connection errors, will retry
                pass

            except asyncio.CancelledError:
                # Graceful close before exiting
                if self._websocket is not None:
                    await asyncio.wait_for(self._websocket.close(), self._close_timeout)
                    self._websocket = None
                return

            except Exception as e:
                logger.error(f"{Fore.RED}[ERROR] WebSocket operation failed: {e}{Style.RESET_ALL}")

            finally:
                # Close websocket if still open (for non-cancel cases)
                if self._websocket is not None:
                    await asyncio.wait_for(self._websocket.close(), timeout=self._close_timeout)
                    self._websocket = None
                    self._device.on_transport_disconnected(Transport.WIFI)

            # Wait before reconnecting (only if not stopping)
            if not self._device.is_stop_flag_set():
                try:
                    await asyncio.sleep(self._reconnect_delay)
                except asyncio.CancelledError:
                    # Expected behavior on task cancellation, exit gracefully
                    return

    async def _websocket_receiver(self, ws: ClientConnection) -> None:
        try:
            async for raw_data in ws:
                if self._device.is_stop_flag_set():
                    break

                message = raw_data.strip()
                if not message:
                    # Ignore empty messages
                    continue

                try:
                    logger.debug(f"{Fore.MAGENTA}RX (WebSocket): {message}{Style.RESET_ALL}")
                    self._device.decode_and_handle_message(message)

                except json.JSONDecodeError:
                    logger.warning(f"{Fore.YELLOW}[WARNING] Non-JSON data received: {message}{Style.RESET_ALL}")

                except Exception as e:
                    logger.error(f"{Fore.RED}[ERROR] Error decoding message: {e}{Style.RESET_ALL}")

        except ConnectionClosed:
            return  # Connection closed, exit receiver

    def send(self, message: str) -> None:
        """
        Sends a text message via the active WebSocket connection.
        """
        if self._websocket is not None:
            logger.debug(f"{Fore.GREEN}TX (WebSocket): {message.strip()}{Style.RESET_ALL}")
            asyncio.create_task(self._websocket.send(message))
