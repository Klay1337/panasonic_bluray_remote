"""Panasonic Blu-ray Player API Client.

This module provides direct HTTP communication with Panasonic Blu-ray players
without requiring the panacotta library. Based on reverse-engineered API findings.
"""
from __future__ import annotations

import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from enum import Enum
from typing import Any

_LOGGER = logging.getLogger(__name__)

# API Configuration
ENDPOINT_PATH = "/WAN/dvdr/dvdr_ctrl.cgi"
USER_AGENT = "MEI-LAN-REMOTE-CALL"
DEFAULT_TIMEOUT = 5


class DeviceMode(Enum):
    """Device mode from STATUS_SIMPLE field_03."""
    IDLE = "00"
    TRAY_OPEN = "01"
    REWIND = "02"
    FAST_FORWARD = "05"
    SLOW_MOTION = "06"
    STANDBY = "07"
    PLAYING = "08"
    PAUSED = "09"
    UNKNOWN = "FF"


class PlaybackState(Enum):
    """Playback state from PST field_0."""
    STOPPED = "0"
    PLAYING = "1"
    PAUSED = "2"
    FAST_FORWARD = "4"
    REWIND = "5"
    SLOW_MOTION = "6"
    UNKNOWN = "99"


@dataclass
class PlayerStatus:
    """Player status data."""
    is_on: bool
    device_mode: DeviceMode
    playback_state: PlaybackState
    position_seconds: int
    speed_multiplier: int
    clock_time: str | None
    raw_pst: str | None
    raw_status: str | None


class PanasonicBlurayAPI:
    """API client for Panasonic Blu-ray players."""

    # Command mappings
    COMMANDS = {
        # Power
        "POWER": "cCMD_RC_POWER",
        "POWERON": "cCMD_RC_POWERON",
        "POWEROFF": "cCMD_RC_POWEROFF",

        # Playback
        "PLAYBACK": "cCMD_RC_PLAYBACK",
        "PLAY": "cCMD_RC_PLAYBACK",
        "PAUSE": "cCMD_RC_PAUSE",
        "STOP": "cCMD_RC_STOP",
        "MEDIA_PLAY": "cCMD_RC_PLAYBACK",
        "MEDIA_PAUSE": "cCMD_RC_PAUSE",
        "MEDIA_PLAY_PAUSE": "cCMD_RC_PAUSE",
        "MEDIA_STOP": "cCMD_RC_STOP",

        # Navigation
        "UP": "cCMD_RC_UP",
        "DOWN": "cCMD_RC_DOWN",
        "LEFT": "cCMD_RC_LEFT",
        "RIGHT": "cCMD_RC_RIGHT",
        "DPAD_UP": "cCMD_RC_UP",
        "DPAD_DOWN": "cCMD_RC_DOWN",
        "DPAD_LEFT": "cCMD_RC_LEFT",
        "DPAD_RIGHT": "cCMD_RC_RIGHT",
        "DPAD_CENTER": "cCMD_RC_SELECT",
        "SELECT": "cCMD_RC_SELECT",
        "OK": "cCMD_RC_SELECT",
        "RETURN": "cCMD_RC_RETURN",
        "BACK": "cCMD_RC_RETURN",
        "EXIT": "cCMD_RC_EXIT",
        "HOME": "cCMD_RC_MLTNAVI",
        "MENU": "cCMD_RC_MENU",
        "TITLE": "cCMD_RC_TITLE",
        "POPUP": "cCMD_RC_PUPMENU",
        "PUPMENU": "cCMD_RC_PUPMENU",
        "SETUP": "cCMD_RC_SETUP",

        # Skip / Chapter
        "SKIPFWD": "cCMD_RC_SKIPFWD",
        "SKIPREV": "cCMD_RC_SKIPREV",
        "NEXT": "cCMD_RC_SKIPFWD",
        "PREV": "cCMD_RC_SKIPREV",
        "PREVIOUS": "cCMD_RC_SKIPREV",
        "MEDIA_NEXT": "cCMD_RC_SKIPFWD",
        "MEDIA_PREVIOUS": "cCMD_RC_SKIPREV",

        # Fast Forward
        "CUE": "cCMD_RC_CUE",
        "FF": "cCMD_RC_CUE",
        "SEARCH_FWD1": "cCMD_RC_SEARCH_FWD1",
        "SEARCH_FWD2": "cCMD_RC_SEARCH_FWD2",
        "SEARCH_FWD3": "cCMD_RC_SEARCH_FWD3",
        "SEARCH_FWD4": "cCMD_RC_SEARCH_FWD4",
        "SEARCH_FWD5": "cCMD_RC_SEARCH_FWD5",

        # Rewind
        "REV": "cCMD_RC_REV",
        "REW": "cCMD_RC_REV",
        "SEARCH_REV1": "cCMD_RC_SEARCH_REV1",
        "SEARCH_REV2": "cCMD_RC_SEARCH_REV2",
        "SEARCH_REV3": "cCMD_RC_SEARCH_REV3",
        "SEARCH_REV4": "cCMD_RC_SEARCH_REV4",
        "SEARCH_REV5": "cCMD_RC_SEARCH_REV5",

        # Slow Motion
        "SLOW_FWD1": "cCMD_RC_SLOW_FWD1",
        "SLOW_FWD2": "cCMD_RC_SLOW_FWD2",
        "SLOW_FWD3": "cCMD_RC_SLOW_FWD3",
        "SLOW_FWD4": "cCMD_RC_SLOW_FWD4",
        "SLOW_FWD5": "cCMD_RC_SLOW_FWD5",

        # Frame Advance
        "FRAMEADV": "cCMD_RC_FRAMEADV",
        "REVERSEFRAMEADV": "cCMD_RC_REVERSEFRAMEADV",

        # Tray
        "OP_CL": "cCMD_RC_OP_CL",
        "EJECT": "cCMD_RC_OP_CL",
        "TRAYOPEN": "cCMD_RC_TRAYOPEN",
        "TRAYCLOSE": "cCMD_RC_TRAYCLOSE",

        # Color buttons
        "RED": "cCMD_RC_RED",
        "GREEN": "cCMD_RC_GREEN",
        "YELLOW": "cCMD_RC_YELLOW",
        "BLUE": "cCMD_RC_BLUE",

        # Numbers
        "D0": "cCMD_RC_D0",
        "D1": "cCMD_RC_D1",
        "D2": "cCMD_RC_D2",
        "D3": "cCMD_RC_D3",
        "D4": "cCMD_RC_D4",
        "D5": "cCMD_RC_D5",
        "D6": "cCMD_RC_D6",
        "D7": "cCMD_RC_D7",
        "D8": "cCMD_RC_D8",
        "D9": "cCMD_RC_D9",
        "0": "cCMD_RC_D0",
        "1": "cCMD_RC_D1",
        "2": "cCMD_RC_D2",
        "3": "cCMD_RC_D3",
        "4": "cCMD_RC_D4",
        "5": "cCMD_RC_D5",
        "6": "cCMD_RC_D6",
        "7": "cCMD_RC_D7",
        "8": "cCMD_RC_D8",
        "9": "cCMD_RC_D9",

        # Audio/Video settings
        "AUDIOSEL": "cCMD_RC_AUDIOSEL",
        "AUDIO": "cCMD_RC_AUDIOSEL",
        "SUB_TITLE": "cCMD_RC_SUB_TITLE",
        "SUBTITLE": "cCMD_RC_SUB_TITLE",
        "DETAIL": "cCMD_RC_DETAIL",
        "INFO": "cCMD_RC_DETAIL",
        "DSPSEL": "cCMD_RC_DSPSEL",
        "DISPLAY": "cCMD_RC_DSPSEL",
        "OSDONOFF": "cCMD_RC_OSDONOFF",
        "3D": "cCMD_RC_3D",
        "PICTMD": "cCMD_RC_PICTMD",
        "PICTURESETTINGS": "cCMD_RC_PICTURESETTINGS",
        "HDR_PICTUREMODE": "cCMD_RC_HDR_PICTUREMODE",

        # Apps
        "NETFLIX": "cCMD_RC_NETFLIX",
        "NETWORK": "cCMD_RC_NETWORK",
        "MIRACAST": "cCMD_RC_MIRACAST",
    }

    def __init__(self, host: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Initialize the API client."""
        self._host = host
        self._timeout = timeout
        self._endpoint = f"http://{host}{ENDPOINT_PATH}"

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    def _send_raw(self, data: str) -> tuple[bool, str | None, list[str]]:
        """Send raw POST data to the device.

        Returns:
            Tuple of (success, response_code, data_lines)
        """
        try:
            request = urllib.request.Request(
                self._endpoint,
                data=data.encode("utf-8"),
                headers={"User-Agent": USER_AGENT},
            )

            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                lines = raw.split("\r\n")

                # Parse response code from first line
                response_code = None
                if lines:
                    first = lines[0]
                    if "," in first:
                        response_code = first.split(",", 1)[0]
                    else:
                        response_code = first

                # Data lines (skip first line, skip empty)
                data_lines = [line for line in lines[1:] if line.strip()]

                success = response_code == "00"
                return success, response_code, data_lines

        except urllib.error.HTTPError as e:
            _LOGGER.debug("HTTP error %s: %s", e.code, e.reason)
            return False, None, []
        except urllib.error.URLError as e:
            _LOGGER.debug("URL error: %s", e.reason)
            return False, None, []
        except Exception as e:
            _LOGGER.debug("Request error: %s", e)
            return False, None, []

    def send_command(self, command: str) -> tuple[bool, str | None]:
        """Send a command to the device.

        Args:
            command: Command name (e.g., "POWER", "PLAY", "PAUSE")

        Returns:
            Tuple of (success, response_code)
        """
        # Map command name to API command
        cmd_upper = command.upper()
        if cmd_upper in self.COMMANDS:
            api_cmd = self.COMMANDS[cmd_upper]
        elif command.startswith("cCMD_"):
            api_cmd = command
        else:
            # Try with RC_ prefix
            api_cmd = f"cCMD_RC_{cmd_upper}"

        data = f"{api_cmd}.x=100&{api_cmd}.y=100"
        success, code, _ = self._send_raw(data)

        _LOGGER.debug("Command %s (%s): %s", command, api_cmd, "OK" if success else f"FAIL ({code})")
        return success, code

    def send_key(self, key: str) -> tuple[str, str]:
        """Send a key press (compatibility method).

        This method provides compatibility with the panacotta library interface.

        Args:
            key: Key name to send

        Returns:
            Tuple of (status, message) for compatibility
        """
        success, code = self.send_command(key)
        if success:
            return ("ok", "")
        return ("error", code or "unknown")

    def get_status(self) -> tuple[str, int, int]:
        """Get play status (compatibility method).

        This method provides compatibility with the panacotta library interface.

        Returns:
            Tuple of (state, position, duration)
        """
        status = self.get_player_status()

        if status is None:
            return ("error", -1, -1)

        if not status.is_on:
            return ("standby", 0, 0)

        # Map playback state to panacotta-compatible strings
        state_map = {
            PlaybackState.STOPPED: "stopped",
            PlaybackState.PLAYING: "playing",
            PlaybackState.PAUSED: "paused",
            PlaybackState.FAST_FORWARD: "playing",
            PlaybackState.REWIND: "playing",
            PlaybackState.SLOW_MOTION: "playing",
        }

        state = state_map.get(status.playback_state, "off")
        return (state, status.position_seconds, 0)

    def get_play_status(self) -> tuple[str, int, int]:
        """Alias for get_status for compatibility."""
        return self.get_status()

    def get_player_status(self) -> PlayerStatus | None:
        """Get comprehensive player status.

        Returns:
            PlayerStatus object or None on error
        """
        # Get PST (play status)
        pst_data = f"cCMD_PST.x=100&cCMD_PST.y=100"
        pst_success, _, pst_lines = self._send_raw(pst_data)

        # Get STATUS_SIMPLE
        status_data = f"cCMD_RC_STATUS_SIMPLE.x=100&cCMD_RC_STATUS_SIMPLE.y=100"
        status_success, _, status_lines = self._send_raw(status_data)

        if not pst_success or not status_success:
            return None

        # Parse PST
        playback_state = PlaybackState.UNKNOWN
        position_seconds = 0
        speed_multiplier = 0
        raw_pst = None

        if pst_lines:
            raw_pst = pst_lines[0]
            parts = raw_pst.split(",")
            if len(parts) >= 3:
                # Field 0: playback state
                state_val = parts[0]
                for ps in PlaybackState:
                    if ps.value == state_val:
                        playback_state = ps
                        break

                # Field 1: position in seconds
                try:
                    position_seconds = int(parts[1])
                except ValueError:
                    pass

                # Field 2: speed multiplier
                try:
                    speed_multiplier = int(parts[2])
                except ValueError:
                    pass

        # Parse STATUS_SIMPLE
        is_on = True
        device_mode = DeviceMode.UNKNOWN
        clock_time = None
        raw_status = None

        if status_lines:
            raw_status = status_lines[0]
            parts = raw_status.split(",")
            if len(parts) >= 14:
                # Field 3: device mode
                mode_val = parts[3]
                for dm in DeviceMode:
                    if dm.value == mode_val:
                        device_mode = dm
                        break

                # Check power state
                is_on = device_mode != DeviceMode.STANDBY

                # Field 13: clock time
                clock_time = parts[13] if parts[13] else None

        return PlayerStatus(
            is_on=is_on,
            device_mode=device_mode,
            playback_state=playback_state,
            position_seconds=position_seconds,
            speed_multiplier=speed_multiplier,
            clock_time=clock_time,
            raw_pst=raw_pst,
            raw_status=raw_status,
        )

    def is_tray_open(self) -> bool | None:
        """Check if the disc tray is open.

        Returns:
            True if open, False if closed, None on error
        """
        status = self.get_player_status()
        if status is None:
            return None
        return status.device_mode == DeviceMode.TRAY_OPEN

    def open_tray(self) -> bool:
        """Open the disc tray."""
        success, _ = self.send_command("TRAYOPEN")
        return success

    def close_tray(self) -> bool:
        """Close the disc tray."""
        success, _ = self.send_command("TRAYCLOSE")
        return success

    def toggle_tray(self) -> bool:
        """Toggle the disc tray open/closed."""
        success, _ = self.send_command("OP_CL")
        return success

    def power_on(self) -> bool:
        """Power on the device."""
        success, _ = self.send_command("POWERON")
        return success

    def power_off(self) -> bool:
        """Power off the device (standby)."""
        success, _ = self.send_command("POWEROFF")
        return success

    def play(self) -> bool:
        """Start playback."""
        success, _ = self.send_command("PLAYBACK")
        return success

    def pause(self) -> bool:
        """Pause playback."""
        success, _ = self.send_command("PAUSE")
        return success

    def stop(self) -> bool:
        """Stop playback."""
        success, _ = self.send_command("STOP")
        return success

    def next_track(self) -> bool:
        """Skip to next chapter/track."""
        success, _ = self.send_command("SKIPFWD")
        return success

    def previous_track(self) -> bool:
        """Skip to previous chapter/track."""
        success, _ = self.send_command("SKIPREV")
        return success
