import logging
from homeassistant import config_entries
import voluptuous as vol
import aiohttp
from .const import DOMAIN  # Ensure const.py defines DOMAIN

_LOGGER = logging.getLogger(__name__)

async def validate_token_and_get_pat(email, token):
    """Validate the token with the backend and return the GitHub PAT on success."""
    url = "https://smarti.pythonanywhere.com/validate-token"
    payload = {"email": email, "token": token}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                _LOGGER.debug(f"Response status: {response.status}")
                response_text = await response.text()
                _LOGGER.debug(f"Raw response: {response_text}")
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(f"Parsed JSON: {data}")
                    if data.get("status") == "success":
                        _LOGGER.info("Subscription validation successful.")
                        return data.get("github_pat")
                    else:
                        _LOGGER.error("Invalid subscription status in response.")
                else:
                    _LOGGER.error(f"Failed with HTTP status: {response.status}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"Error during token validation: {e}")

    return None

@config_entries.HANDLERS.register(DOMAIN)
class SmartiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMARTi PowerFlow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            email = user_input["email"]
            token = user_input["token"]

            github_pat = await validate_token_and_get_pat(email, token)
            if github_pat:
                # Success! Create the entry with the GitHub PAT.
                _LOGGER.info("Configuration entry for SMARTi PowerFlow creation successful.")
                return self.async_create_entry(
                    title="SMARTi PowerFlow™",
                    data={"email": email, "token": token, "github_pat": github_pat},
                )
            else:
                errors["base"] = "invalid_token"

        schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("token"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
