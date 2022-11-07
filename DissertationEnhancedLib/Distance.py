from DissertationEnhancedLib.CustomExceptions import InvalidArgumentTypeException


class Distance:
    def __init__(self, x:float, y:float, xy:float):
        if (type(x) is not float or type(y) is not float or type(xy) is not float):
            raise InvalidArgumentTypeException()

        self.x = x
        self.y = y
        self.xy = xy
        # changes to this will break loading graphs and requires fixing __str__ and __repr__ function

    def __str__(self) -> str:
        return f'({self.x}, {self.y}, {self.xy})'
    
    def __repr__(self) -> str:
        return f'Distance({self.x}, {self.y}, {self.xy})'
