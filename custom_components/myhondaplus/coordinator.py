"""Data coordinator for My Honda+."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymyhondaplus.api import HondaAPI, HondaAPIError, parse_ev_status

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_PERSONAL_ID,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_USER_ID,
    CONF_VIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

logger = logging.getLogger(__name__)


class HondaDataUpdateCoordinator(DataUpdateCoordinator[dict]):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.vin: str = entry.data[CONF_VIN]
        self.api = HondaAPI()
        self._apply_tokens()

        interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    def _apply_tokens(self) -> None:
        self.api.set_tokens(
            access_token=self.entry.data[CONF_ACCESS_TOKEN],
            refresh_token=self.entry.data[CONF_REFRESH_TOKEN],
            personal_id=self.entry.data.get(CONF_PERSONAL_ID, ""),
            user_id=self.entry.data.get(CONF_USER_ID, ""),
        )

    def _persist_tokens_if_changed(self) -> None:
        tokens = self.api.tokens
        data = self.entry.data
        if (tokens.access_token != data.get(CONF_ACCESS_TOKEN)
                or tokens.refresh_token != data.get(CONF_REFRESH_TOKEN)):
            new_data = {**data,
                        CONF_ACCESS_TOKEN: tokens.access_token,
                        CONF_REFRESH_TOKEN: tokens.refresh_token}
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)

    def _fetch_data(self) -> dict:
        dashboard = self.api.get_dashboard_cached(self.vin)
        return parse_ev_status(dashboard)

    async def _async_update_data(self) -> dict:
        try:
            data = await self.hass.async_add_executor_job(self._fetch_data)
        except HondaAPIError as err:
            self._persist_tokens_if_changed()
            if err.status_code == 401:
                raise ConfigEntryAuthFailed from err
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(str(err)) from err

        self._persist_tokens_if_changed()
        return data

    async def async_refresh_from_car(self) -> None:
        await self.hass.async_add_executor_job(
            self.api.request_dashboard_refresh, self.vin,
        )
        self._persist_tokens_if_changed()

    async def async_send_command(self, func, *args) -> str:
        result = await self.hass.async_add_executor_job(func, *args)
        self._persist_tokens_if_changed()
        return result
