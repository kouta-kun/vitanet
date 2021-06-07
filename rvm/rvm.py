import enum
import inspect
from typing import Dict

import numpy as np

from autoexpanding_map import AutoExpandingMap
from map import TileType
from . import player_function


class Direction(enum.Enum):
    N = enum.auto()
    S = enum.auto()
    E = enum.auto()
    W = enum.auto()


class RVMPersistentContext:
    def __init__(self):
        self.actors = {}
        self.actor_scripts: Dict[int, RVMScript] = {}
        self.actor_id_counter = 0
        self.chunk_shape = (32, 32)
        self.simulation_map = AutoExpandingMap(self.chunk_shape)
        self.frame_count = 0

    def introspect_actor(self, attribute, viewing_actor, observed_actor):
        if observed_actor in self.actors and attribute in self.actors[observed_actor]:
            return self.actors[observed_actor][attribute]
        return None

    def create_player(self, player_name):
        return self.add_actor(PLAYER_SCRIPT_GEN(player_name))

    def inspect_position(self, viewing_actor, x, y):
        return self.simulation_map[x, y]

    def look_direction(self, direction: Direction, viewing_actor):
        viewer_position = list(self.actors[viewing_actor]['position'])
        if direction == Direction.N:
            viewer_position[1] -= 1
        elif direction == Direction.S:
            viewer_position[1] += 1
        elif direction == Direction.W:
            viewer_position[0] -= 1
        elif direction == Direction.E:
            viewer_position[0] += 1
        positioned_actor = list(filter(lambda k: self.actors[k]['position'] == viewer_position, self.actors.keys()))
        return viewer_position, positioned_actor[0] if len(positioned_actor) > 0 else None

    def move_direction(self, direction: Direction, actor_id):
        viewer_position = self.actors[actor_id]['position']
        if direction == Direction.N:
            viewer_position[1] -= 1
        elif direction == Direction.S:
            viewer_position[1] += 1
        elif direction == Direction.W:
            viewer_position[0] -= 1
        elif direction == Direction.E:
            viewer_position[0] += 1

    def step(self):
        for a in self.actors:
            if self.actors[a]['enabled']:
                self.actor_scripts[a].execute(self, a)
                self.actors[a]['messages'] = list(
                    filter(lambda m: (self.frame_count - m['timestamp']) < (4 * 15), self.actors[a]['messages']))
        self.frame_count += 1

    def send_message(self, sending_actor, message):
        self.actors[sending_actor]['messages'].append({'timestamp': self.frame_count, 'msg': message})

    def add_actor(self, script):
        x = np.random.randint(-5, 5)
        y = np.random.randint(-5, 5)
        self.actors[self.actor_id_counter] = {'position': [x, y],
                                              'enabled': True,
                                              'creation_time': self.frame_count,
                                              'name': script.name,
                                              'messages': []}
        self.actor_scripts[self.actor_id_counter] = script
        self.actor_id_counter += 1
        return self.actor_id_counter - 1

    def look_actor(self, viewing_actor, observed_actor):
        vx, vy = self.actors[viewing_actor]['position']
        ox, oy = self.actors[observed_actor]['position']
        xdelta = vx - ox
        ydelta = vy - oy
        dist = (xdelta ** 2 + ydelta ** 2) ** .5
        if dist < 10:
            return (ox, oy), observed_actor
        else:
            return (None, None), observed_actor

    def inspect_world(self, actor_id):
        x, y = zip(*self.simulation_map.chunks.keys())

        x1 = min(x)
        x2 = max(x)
        y1 = min(y)
        y2 = max(y)

        return x2 - x1, y2 - y1

    def status_of(self, user_id):
        if user_id in self.actors and self.actors[user_id]['enabled']:
            return self.actor_scripts[user_id].status(self, user_id)
        else:
            return {'error': 'unknown or disabled actor'}


class RVMTemporaryContext:
    persistent_context: RVMPersistentContext

    def __init__(self, persistent_context: RVMPersistentContext, actor_id):
        self.persistent_context = persistent_context
        self.actor_id = actor_id


class RVMScript:
    def __init__(self, source, name, **kwargs):
        self.source = source
        self.environment = {**kwargs, 'name': name, 'direction': Direction, 'tiletype_TYPE': TileType}
        self.name = name
        exec(source, self.environment)

    def status(self, persistent_ctx: RVMPersistentContext, actor_id):
        rvmTemporaryCtx = RVMTemporaryContext(persistent_ctx, actor_id)
        try:
            return eval('status(ctx)', self.environment, {'ctx': rvmTemporaryCtx})
        except Exception as e:
            print('got exception', e, 'executing script', self)
            raise ValueError(e, self)

    def execute(self, persistent_ctx: RVMPersistentContext, actor_id):
        rvmTemporaryCtx = RVMTemporaryContext(persistent_ctx, actor_id)
        try:
            eval('step(ctx)', self.environment, {'ctx': rvmTemporaryCtx})
        except Exception as e:
            print('got exception', e, 'executing script', self)
            raise ValueError(e, self)


PLAYER_SCRIPT_GEN = lambda name: RVMScript(inspect.getsource(player_function), name=name)
