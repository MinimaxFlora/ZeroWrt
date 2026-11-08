"""Validated build settings.

Values arrive from workflow inputs or ``ZEROWRT_*`` environment variables.  They
are checked before the source tree is touched: a malformed address or SSID must
never reach a regular expression that rewrites ``config_generate``.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass, replace
from urllib.parse import urlparse

from . import profiles, util

DEFAULT_ROOT_PASSWORD = ""
DEFAULT_WIFI_NAME = "ZeroWrt"
DEFAULT_WIFI_PASSWORD = "1234567890"
DEFAULT_DIST_NAME = "ZeroWrt"
DEFAULT_LAN_IP = profiles.DEFAULT_LAN_IP
DEFAULT_OTA_URL = "https://ota.tatalvpai.vip/ota.json"
DEFAULT_OTA_CNAME = "ota.tatalvpai.vip"

DEVICE_RE = re.compile(r"[A-Za-z0-9_.-]{1,64}")
DIST_RE = re.compile(r"[A-Za-z0-9_.-]{1,32}")
WIFI_NAME_RE = re.compile(r"[\w .-]+", re.UNICODE)
WIFI_PASSWORD_RE = re.compile(r"[A-Za-z0-9!@#%^&*()_+.:=?\-]{8,63}")


@dataclass(frozen=True)
class BuildSettings:
    """Validated user supplied settings."""

    device: str = profiles.DEFAULT_DEVICE
    lan_ip: str = DEFAULT_LAN_IP
    root_password: str = DEFAULT_ROOT_PASSWORD
    wifi_name: str = DEFAULT_WIFI_NAME
    wifi_password: str = DEFAULT_WIFI_PASSWORD
    dist_name: str = DEFAULT_DIST_NAME
    ota_url: str = DEFAULT_OTA_URL

    def __post_init__(self) -> None:
        """Validate even when the dataclass is constructed directly."""
        self.validated()

    @classmethod
    def from_environment(cls, env: dict[str, str] | None = None) -> BuildSettings:
        values = os.environ if env is None else env
        return cls(
            device=values.get("ZEROWRT_DEVICE") or profiles.DEFAULT_DEVICE,
            lan_ip=values.get("ZEROWRT_LAN_IP") or values.get("ZEROWRT_IP") or DEFAULT_LAN_IP,
            root_password=values.get("ZEROWRT_ROOT_PASSWORD", ""),
            wifi_name=values.get("ZEROWRT_WIFI_NAME") or DEFAULT_WIFI_NAME,
            wifi_password=values.get("ZEROWRT_WIFI_PASSWORD") or DEFAULT_WIFI_PASSWORD,
            dist_name=values.get("ZEROWRT_DIST") or DEFAULT_DIST_NAME,
            ota_url=values.get("ZEROWRT_OTA_URL") or DEFAULT_OTA_URL,
        )

    def with_overrides(self, **values: str | None) -> BuildSettings:
        """Return a copy where every non-None value replaces the current one."""
        current = {field: getattr(self, field) for field in self.__dataclass_fields__}
        for key, value in values.items():
            if value is not None:
                current[key] = value
        return replace(self, **current)

    def profile(self) -> profiles.DeviceProfile:
        return profiles.require(self.device)

    def effective_ip(self) -> str:
        """The unified LAN IP written into ``config_generate``."""
        return self.lan_ip or DEFAULT_LAN_IP

    def ssid(self, band: str) -> str:
        suffix = {"2g": "2.4G", "5g": "5G", "6g": "6G"}.get(band, band.upper())
        return f"{self.wifi_name}-{suffix}"

    def validated(self) -> BuildSettings:
        profiles.require(self.device)
        if not DEVICE_RE.fullmatch(self.device):
            raise util.BuildError(f"invalid device profile name: {self.device!r}")

        if self.lan_ip:
            try:
                address = ipaddress.ip_address(self.lan_ip)
            except ValueError as exc:
                raise util.BuildError(f"invalid LAN IP address: {self.lan_ip!r}") from exc
            if address.version != 4:
                raise util.BuildError(f"LAN IP address must be IPv4: {self.lan_ip!r}")
            if address.is_multicast or address.is_unspecified or address.is_loopback:
                raise util.BuildError(f"LAN IP address is not usable: {self.lan_ip!r}")

        if not self.root_password:
            raise util.BuildError("root password is required (8-128 characters)")
        if "\n" in self.root_password or "\r" in self.root_password:
            raise util.BuildError("root password must be a single non-empty line")
        if not 8 <= len(self.root_password) <= 128:
            raise util.BuildError("root password must be 8-128 characters")

        if not self.wifi_name or self.wifi_name != self.wifi_name.strip():
            raise util.BuildError("WiFi name must not be empty or padded with spaces")
        if not WIFI_NAME_RE.fullmatch(self.wifi_name):
            raise util.BuildError("WiFi name may only contain letters, digits, spaces, dot, dash and underscore")
        if len(self.wifi_name.encode("utf-8")) > 32:
            raise util.BuildError("WiFi name must be at most 32 bytes (UTF-8)")
        for band in ("2g", "5g", "6g"):
            if len(self.ssid(band).encode("utf-8")) > 32:
                raise util.BuildError(f"WiFi SSID is longer than 32 bytes: {self.ssid(band)!r}")

        if not WIFI_PASSWORD_RE.fullmatch(self.wifi_password or ""):
            raise util.BuildError("WiFi password must be 8-63 characters using letters, digits and !@#%^&*()_+.:=?-")

        if not DIST_RE.fullmatch(self.dist_name) or self.dist_name != self.dist_name.strip():
            raise util.BuildError(f"invalid distribution name: {self.dist_name!r}")

        if self.ota_url:
            parsed = urlparse(self.ota_url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise util.BuildError(f"invalid OTA index URL: {self.ota_url!r}")

        return self
