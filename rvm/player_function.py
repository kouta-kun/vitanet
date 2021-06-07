act = None
direction: type
tiletype_TYPE: type


def status(ctx):
    viewpos = ctx.persistent_context.introspect_actor('position', ctx.actor_id, ctx.actor_id)
    height, tiletype = ctx.persistent_context.inspect_position(ctx.actor_id, *viewpos)
    return {'height': int(height), 'type': tiletype_TYPE(tiletype).name, 'pos': list(viewpos)}


def step(ctx):
    global act
    if act is not None:
        if type(act) is dict:
            act, extra = act['act'], act['args']
            if act == 'MOVE':
                if extra == 'UP':
                    ctx.persistent_context.move_direction(direction.N, ctx.actor_id)
                elif extra == 'DOWN':
                    ctx.persistent_context.move_direction(direction.S, ctx.actor_id)
                elif extra == 'LEFT':
                    ctx.persistent_context.move_direction(direction.W, ctx.actor_id)
                elif extra == 'RIGHT':
                    ctx.persistent_context.move_direction(direction.E, ctx.actor_id)
                else:
                    print('UNKNOWN DIRECTION:', extra)
            elif act == 'MESSAGE':
                ctx.persistent_context.send_message(ctx.actor_id, extra)
            else:
                print("UNKNOWN ACTION:", act)
        act = None
