import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_LOCATION
)
import voluptuous as vol

from reverse_geocoder import ReverseGeocoder

DOMAIN = 'reverse_geocode'

VALID_PROVIDERS = [

]

ATTR_PERSON = 'person'
ATTR_PROVIDER = 'provider'

CONF_PROVIDER = 'provider'
CONF_KEY = 'key'

SERVICE_REVERSE_GEOCODE = "reverse_geocode"
SERVICE_PROVIDER_REVERSE_GEOCODE = "%s_reverse_geocode"

PROVIDER_REVERSE_GEOCODE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Exclusive(ATTR_ENTITY_ID, "location"): cv.entity_id,
        vol.Exclusive(ATTR_PERSON, "location"): cv.string,
        vol.Exclusive(ATTR_LOCATION, "location"): cv.gps
    }
)


def dict_schema(key_schema, value_schema):
    """Ensure dicts have valid as keys."""
    schema = vol.Schema({
        str: value_schema
    })

    def verify(value):
        """Validate all keys are valid and then the value_schema."""
        if not isinstance(value, dict):
            raise vol.Invalid('expected dictionary')

        for key in value.keys():
            key_schema(key)

        return schema(value)
    return verify


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: dict_schema(
        vol.All(str, vol.In(VALID_PROVIDERS)),
        vol.Schema({
            vol.Optional(CONF_KEY): cv.string
        })
    )
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Setup the reverse_geocode component"""
    hass.data[DOMAIN] = {}

    if not config[DOMAIN]:
        return True

    configured_providers = []

    for provider, provider_config in config[DOMAIN].items:
        hass.data[DOMAIN][provider] = ReverseGeocoder(
            hass,
            provider,
            provider_config.get(CONF_KEY, None)
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_PROVIDER_REVERSE_GEOCODE,
            hass.data[DOMAIN][provider].reverse_geocode,
            schema=PROVIDER_REVERSE_GEOCODE_SERVICE_SCHEMA
        )
        configured_providers.append(provider)

    async def reverse_geocode(service):
        await hass.data[DOMAIN][service.data[ATTR_PROVIDER]].reverse_geocode(service)

    hass.services.async_register(
        DOMAIN,
        SERVICE_REVERSE_GEOCODE,
        reverse_geocode,
        schema=PROVIDER_REVERSE_GEOCODE_SERVICE_SCHEMA.extend({
            vol.Required(ATTR_PROVIDER): vol.All(
                cv.string,
                vol.In(configured_providers)
            )
        })
    )

    return True
