from typing import Dict, Tuple

import numpy as np

import visualization
from map import SimulationMap


class AutoExpandingMap:
    def render_chunk(self, chunk_x, chunk_y):
        self.assert_exist_chunk((chunk_x, chunk_y))
        img = np.zeros((self.chunk_y * 16, self.chunk_x * 16, 3), dtype=np.uint8)
        for x in range(self.chunk_x):
            for y in range(self.chunk_y):
                img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16, :] = self.tilemap[
                    self.chunks[(chunk_x, chunk_y)].type_map[x, y]]
        return img

    def __init__(self, chunk_shape):
        self.chunks: Dict[Tuple[int, int], SimulationMap] = {}
        self.chunk_x, self.chunk_y = chunk_shape
        self.tilemap = visualization.TileSet(16)

    def __getitem__(self, args):
        x, y = args
        chunk_x, inchunk_x = divmod(x, self.chunk_x)
        chunk_y, inchunk_y = divmod(y, self.chunk_y)
        chunk_index = (chunk_x, chunk_y)
        self.assert_exist_chunk(chunk_index)
        return self.chunks[chunk_index].height_map[inchunk_x, inchunk_y], \
               self.chunks[chunk_index].type_map[inchunk_x, inchunk_y]

    def assert_exist_chunk(self, chunk_index):
        if chunk_index not in self.chunks:
            self.chunks[chunk_index] = SimulationMap((self.chunk_x, self.chunk_y), *chunk_index)
