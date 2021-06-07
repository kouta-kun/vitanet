import enum

import numpy as np
from scipy import ndimage

PERMUTATION_TABLE = [151, 160, 137, 91, 90, 15,  # Hash lookup table as defined by Ken Perlin.  This is a randomly
                     131, 13, 201, 95, 96, 53, 194,  # arranged array of all numbers from 0-255 inclusive.
                     233, 7, 225, 140, 36, 103, 30,
                     69, 142, 8, 99, 37, 240, 21, 10, 23,
                     190, 6, 148, 247, 120, 234, 75, 0, 26,
                     197, 62, 94, 252, 219, 203, 117, 35, 11,
                     32, 57, 177, 33, 88, 237, 149, 56, 87, 174,
                     20, 125, 136, 171, 168, 68, 175, 74, 165, 71,
                     134, 139, 48, 27, 166, 77, 146, 158, 231, 83,
                     111, 229, 122, 60, 211, 133, 230, 220, 105, 92,
                     41, 55, 46, 245, 40, 244, 102, 143, 54, 65, 25,
                     63, 161, 1, 216, 80, 73, 209, 76, 132, 187, 208,
                     89, 18, 169, 200, 196, 135, 130, 116, 188, 159, 86,
                     164, 100, 109, 198, 173, 186, 3, 64, 52, 217, 226,
                     250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85,
                     212, 207, 206, 59, 227, 47, 16, 58, 17, 182, 189, 28, 42,
                     223, 183, 170, 213, 119, 248, 152, 2, 44, 154, 163, 70, 221,
                     153, 101, 155, 167, 43, 172, 9, 129, 22, 39, 253, 19, 98, 108,
                     110, 79, 113, 224, 232, 178, 185, 112, 104, 218, 246, 97, 228,
                     251, 34, 242, 193, 238, 210, 144, 12, 191, 179, 162, 241, 81, 51,
                     145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106, 157,
                     184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205,
                     93, 222, 114, 67, 29, 24, 72, 243, 141, 128, 195, 78, 66, 215, 61, 156, 180
                     ]


def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def grad(hashin, x, y, z):
    h = hashin & 15
    u = x if h < 8 else y
    if h < 4:
        v = y
    elif h == 12 or h == 14:
        v = x
    else:
        v = z
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


def lerp(a, b, x):
    return a + x * (b - a)


class Perlin:
    def __init__(self):
        self.p = []
        for i in range(512):
            self.p.append(PERMUTATION_TABLE[i % 256])

    def perlinhash(self, xi, yi, zi):
        aaa = self.p[self.p[self.p[xi] + yi] + zi]
        aba = self.p[self.p[self.p[xi] + yi + 1] + zi]
        aab = self.p[self.p[self.p[xi] + yi] + zi + 1]
        abb = self.p[self.p[self.p[xi] + yi + 1] + zi + 1]
        baa = self.p[self.p[self.p[xi + 1] + yi] + zi]
        bba = self.p[self.p[self.p[xi + 1] + yi + 1] + zi]
        bab = self.p[self.p[self.p[xi + 1] + yi] + zi + 1]
        bbb = self.p[self.p[self.p[xi + 1] + yi + 1] + zi + 1]
        return aaa, aba, aab, abb, baa, bba, bab, bbb

    def noise3d(self, x, y, z):
        floorX = np.floor(x)
        Xi = int(floorX) & 255

        floorY = np.floor(y)
        Yi = int(floorY) & 255

        floorZ = np.floor(z)
        Zi = int(floorZ) & 255

        xf = x - floorX
        yf = y - floorY
        zf = z - floorZ

        u = fade(xf)
        v = fade(yf)
        w = fade(zf)

        aaa, aba, aab, abb, baa, bba, bab, bbb = self.perlinhash(Xi, Yi, Zi)

        x1 = lerp(grad(aaa, xf, yf, zf), grad(baa, xf - 1, yf, zf), u)
        x2 = lerp(grad(aba, xf, yf - 1, zf), grad(bba, xf - 1, yf - 1, zf), u)

        y1 = lerp(x1, x2, v)

        x1 = lerp(grad(aab, xf, yf, zf - 1),
                  grad(bab, xf - 1, yf, zf - 1),
                  u)

        x2 = lerp(grad(abb, xf, yf - 1, zf - 1),
                  grad(bbb, xf - 1, yf - 1, zf - 1),
                  u)

        y2 = lerp(x1, x2, v)
        return (lerp(y1, y2, w) + 1) / 2


def make_height_map(shape, xM, yM):
    map_array = np.zeros(shape, dtype=np.float32)

    perlin = Perlin()

    for x in range(shape[0]):
        for y in range(shape[1]):
            map_array[x, y] = sum(perlin.noise3d((x / 4) + (xM * (shape[0] / 4)),
                                                 (y / 4) + (yM * (shape[1] / 4)),
                                                 np.random.random_sample()) for i in range(5)) / 5
    return (map_array * 240).astype(np.uint8)


class TileType(enum.Enum):
    WATER = enum.auto()
    SAND = enum.auto()
    GRASS = enum.auto()
    STONE = enum.auto()


def make_type_map(height_map):
    type_array = np.zeros(height_map.shape, dtype=np.uint16)

    water_index = height_map < 70
    water_index = ndimage.binary_erosion(ndimage.binary_dilation(water_index))
    type_array[water_index] = TileType.WATER.value

    sand_index = (type_array == 0) & (height_map < 85)
    sand_index = ndimage.binary_dilation(sand_index | ndimage.binary_dilation(water_index)) & (~ water_index)

    type_array[sand_index] = TileType.SAND.value
    type_array[height_map > 200] = TileType.STONE.value

    type_array[type_array == 0] = TileType.GRASS.value

    return type_array


class SimulationMap:
    def __init__(self, shape, x, y):
        self.height_map = make_height_map(shape, x, y)
        self.type_map = make_type_map(self.height_map)


