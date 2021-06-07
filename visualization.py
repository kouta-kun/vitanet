import cv2

from map import TileType


class TileSet:
    def __init__(self, size):
        tileset = cv2.imread('tileset.png')
        imheight, imwidth, imchan = tileset.shape
        tiletable = []
        for ty in range(0, imheight // size):
            for tx in range(0, imwidth // size):
                tiletable.append(tileset[ty * size:(ty+1)*size, tx * size:(tx+1)*size])
        self.tiles = tiletable
        self.size = size
        self.tilemap = {TileType.GRASS.value: 0, TileType.SAND.value: 8, TileType.WATER.value: 7,
                        TileType.STONE.value: 27}

    def __getitem__(self, item):
        return self.tiles[self.tilemap[item]]

    def __len__(self):
        return len(self.tiles)

    def __neg__(self):
        return self.size
