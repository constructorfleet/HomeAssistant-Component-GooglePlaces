import logging

from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE
)
from homeassistant.core import split_entity_id
from homeassistant.util import slugify
from homeassistant.components.person import (DOMAIN as PERSON_DOMAIN, ATTR_SOURCE)

from . import ATTR_PERSON

import geocoder

_LOGGER = logging.getLogger(__name__)

ATTR_GEOCODED_ADDRESS = 'geocoded_address'


def _remove_domain(entity_id):
    parts = split_entity_id(entity_id)
    if not parts:
        return None
    return slugify(parts[-1].lower())

def _get_entity_id(domain, entity):
    return "%s.%s" % (domain.lower(), entity.lower)


class ReverseGeocoder(object):
    """Reverse geocoder provider."""

    def __init__(self, hass, provider, key):
        self._hass = hass
        self._provider = provider
        self._key = key

    @property
    def provider(self):
        return self._provider

    async def reverse_geocode(self, service):
        latitude = None
        longitude = None
        location = None
        entity = None

        if ATTR_PERSON in service.data:
            person = self._hass.states.get(_get_entity_id(PERSON_DOMAIN, service.data[ATTR_PERSON]))
            entity_id = person.attributes.get(ATTR_SOURCE, None)
        else:
            entity_id = service.data(ATTR_ENTITY_ID, None)

        if entity_id:
            entity = self._hass.states.get(entity_id)
            latitude = entity.attributes.get(ATTR_LATITUDE, None)
            longitude = entity.attributes.get(ATTR_LONGITUDE, None)
        elif ATTR_LOCATION in service.data:
            latitude = service.data[ATTR_LATITUDE]
            longitude = service.data[ATTR_LONGITUDE]

        if latitude and longitude:
            location = [latitude, longitude]

        if not location:
            _LOGGER.error("Unable to determine location from service data: %s" % str(service.data))
            return

        try:
            result = geocoder.get(location, provider=self.provider, method="reverse")
            if result.ok:
                if entity:
                    entity.attributes = \
                        (entity.attributes or {})[ATTR_GEOCODED_ADDRESS] = result.address
                _LOGGER.info('Geocoded address for %f, %f: %s' % (
                    latitude,
                    longitude,
                    result.address
                ))
                return result.address
            else:
                _LOGGER.error(
                    'Error retrieving address from provider %s' % self.provider)
        except Exception as e:
            _LOGGER.error(
                'Error connecting to provider %s: %s'% (
                    self.provider,
                    str(e)
                )
            )

        return None
