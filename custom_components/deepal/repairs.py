import voluptuous as vol
import logging
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TOKEN, CONF_REFRESH_TOKEN, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(hass, issue_id, data):
    return TokenInvalidRepairFlow()


class TokenInvalidRepairFlow(RepairsFlow):

    async def async_step_init(self, user_input=None):
        return await self.async_step_paste_tokens()

    async def async_step_paste_tokens(self, user_input=None):
        """Paste new tokens manually."""
        entry = _get_entry(self.hass)
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            refresh_token = user_input[CONF_REFRESH_TOKEN].strip()
            self.hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_TOKEN: token if token.startswith("Bearer ") else f"Bearer {token}",
                    CONF_REFRESH_TOKEN: refresh_token if refresh_token.startswith("Bearer ") else f"Bearer {refresh_token}",
                    CONF_DEVICE_ID: user_input.get(CONF_DEVICE_ID) or entry.data.get(CONF_DEVICE_ID),
                },
            )
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="paste_tokens",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_DEVICE_ID, description={"suggested_value": ""}): str,
            }),
        )


def _get_entry(hass: HomeAssistant):
    return next(
        e for e in hass.config_entries.async_entries(DOMAIN)
    )
