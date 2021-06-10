class PegTile():
    """
    Class to store info about peg tiles on the grid.
    Currently used to get output bit array for Unity socket and to store coordinates for drawing corresponding rectangles on the video feed.
    """
    def __init__(self):
        self.coords = None
        self.has_peg = False
