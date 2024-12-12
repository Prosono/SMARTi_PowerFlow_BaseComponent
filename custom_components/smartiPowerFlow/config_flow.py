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

    _LOGGER.debug(f"Starting token validation. URL: {url}, Payload: {payload}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                _LOGGER.debug(f"HTTP POST to {url} completed with status: {response.status}")
                
                # Log headers and full response text for debugging
                _LOGGER.debug(f"Response headers: {response.headers}")
                response_text = await response.text()
                _LOGGER.debug(f"Raw response text: {response_text}")

                if response.status == 200:
                    try:
                        data = await response.json()
                        _LOGGER.debug(f"Parsed JSON data: {data}")

                        if data.get("status") == "success":
                            _LOGGER.info("Subscription validation successful. Returning GitHub PAT.")
                            return data.get("github_pat")
                        else:
                            _LOGGER.error(f"Validation failed. Status: {data.get('status')}, Message: {data.get('message', 'No message')}")
                    except Exception as json_err:
                        _LOGGER.error(f"Error parsing JSON response: {json_err}")
                else:
                    _LOGGER.error(f"Failed with HTTP status: {response.status}. Response: {response_text}")

    except aiohttp.ClientError as e:
        _LOGGER.error(f"Error during token validation (ClientError): {e}")
    except Exception as e:
        _LOGGER.error(f"Unexpected error during token validation: {e}")

    return None

@config_entries.HANDLERS.register(DOMAIN)
class SmartiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMARTi PowerFlow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug(f"Starting user step. User input: {user_input}")
        errors = {}

        if user_input is not None:
            email = user_input["email"]
            token = user_input["token"]

            _LOGGER.info(f"Validating token for email: {email}")
            github_pat = await validate_token_and_get_pat(email, token)

            if github_pat:
                _LOGGER.info("Configuration entry for SMARTi PowerFlow creation successful.")
                return self.async_create_entry(
                    title="SMARTi PowerFlow™",
                    data={"email": email, "token": token, "github_pat": github_pat},
                )
            else:
                _LOGGER.error("Token validation failed. Adding 'invalid_token' error.")
                errors["base"] = "invalid_token"

        schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("token"): str,
        })

        _LOGGER.debug(f"Rendering form with schema: {schema} and errors: {errors}")
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
