from functools import partial
import re

from django.core.exceptions import ImproperlyConfigured
from django.urls.conf import _path
from django.urls.resolvers import RoutePattern, RegexPattern, _route_to_regex


class IRoutePattern(RoutePattern):

    def _compile(self, route):
        return re.compile(_route_to_regex(route, self._is_endpoint)[0], re.IGNORECASE)


class IRegexPattern(RegexPattern):

    def _compile(self, regex):
        """Compile and return the given regular expression."""
        try:
            return re.compile(regex, re.IGNORECASE)
        except re.error as e:
            raise ImproperlyConfigured(
                '"%s" is not a valid regular expression: %s' % (regex, e)
            ) from e


ipath = partial(_path, Pattern = IRoutePattern)
re_ipath = partial(_path, Pattern = IRegexPattern)
