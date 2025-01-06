import logging
import os
import asyncio
import aiohttp
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN
from .updater import update_files

_LOGGER = logging.getLogger(__name__)

# Interval for periodic updates (e.g., every hour)
UPDATE_INTERVAL = timedelta(hours=1)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SMARTi PowerFlow integration."""
    _LOGGER.info("Setting up the SMARTi PowerFlow™ integration.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SMARTi PowerFlow from a config entry."""
    _LOGGER.info("Setting up SMARTi PowerFlow™ from config entry.")

    # Store domain data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    # Start the aiohttp session for GitHub API requests
    session = aiohttp.ClientSession()
    github_pat = entry.data.get("github_pat")
    config_data = entry.data

    # Define the periodic update function
    async def periodic_update(_):
        _LOGGER.info("Running periodic update for SMARTi PowerFlow™ integration.")
        await update_files(session, config_data, github_pat)

    # Schedule periodic updates
    hass.data[DOMAIN][entry.entry_id]["update_job"] = async_track_time_interval(
        hass, periodic_update, UPDATE_INTERVAL
    )

    # Run the initial update
    await update_files(session, config_data, github_pat)

    return True

async def clear_specific_files(directory: str, files_to_delete: list):
    """Delete specific files asynchronously."""
    if not os.path.exists(directory):
        _LOGGER.warning(f"Directory {directory} does not exist, skipping file deletion.")
        return
    for filename in files_to_delete:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                await asyncio.to_thread(os.remove, file_path)
                _LOGGER.info(f"Deleted file: {file_path}")
            except Exception as e:
                _LOGGER.error(f"Failed to delete file {file_path}: {e}")
        else:
            _LOGGER.info(f"File {file_path} does not exist or is not a file.")

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info("Unloading SMARTi PowerFlow™ config entry.")

    # Cancel periodic updates
    update_job = hass.data[DOMAIN][entry.entry_id].get("update_job")
    if update_job:
        update_job()

    # Close the aiohttp session
    session = aiohttp.ClientSession()
    await session.close()

    # Remove entry data
    hass.data[DOMAIN].pop(entry.entry_id, None)

    # Paths to clear
    packages_path = "/config/packages/"
    dashboards_path = "/config/dashboards/"

    # Files to delete
    packages_files_to_delete = [
        "smarti_powerflow_package.yaml",
        "smarti_dashboard_package.yaml",
    ]
    dashboards_files_to_delete = [
        "SMARTi_Power_Flow_Dashboard.yaml",
    ]

    # Clear specific files
    try:
        await clear_specific_files(packages_path, packages_files_to_delete)
        _LOGGER.info(f"Cleared specific files in: {packages_path}")
    except Exception as e:
        _LOGGER.error(f"Failed to clear specific files in packages: {e}")

    try:
        await clear_specific_files(dashboards_path, dashboards_files_to_delete)
        _LOGGER.info(f"Cleared specific files in: {dashboards_path}")
    except Exception as e:
        _LOGGER.error(f"Failed to clear specific files in dashboards: {e}")

    return True

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle migration of the config entry if needed."""
    _LOGGER.info(f"Migrating SMARTi PowerFlow™ entry from version {entry.version}")

    current_version = 1

    if entry.version == current_version:
        _LOGGER.info("No migration necessary")
        return True

    # Implement migration logic if needed
    hass.config_entries.async_update_entry(entry, version=current_version)
    _LOGGER.info(f"Migration to version {current_version} successful")
    return True
