import OSMPythonTools.element as osm_element

from DissertationEnhancedLib.CustomExceptions import InvalidArgumentTypeException

class GeographicCoords:
    def __init__(self, lon:float, lat:float):
        if (type(lon) is not float or type(lat) is not float):
            raise InvalidArgumentTypeException()
        
        self.lon = lon;
        self.lat = lat;

    @staticmethod
    def from_element(element:osm_element.Element):
        return GeographicCoords(element.lon(), element.lat())