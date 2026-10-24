"""Keep build/AIR exclusion, distinguish a verified unrelated Java server."""
import psutil

def classify(env):
    if env.get('scope') == 'owned process only during play':
        return env
    blockers, background = [], []
    for item in env['processes']:
        if (item.get('name') or '').lower() not in ('java.exe', 'javaw.exe'):
            blockers.append(item)
            continue
        try:
            p = psutil.Process(item['pid'])
            args = p.cmdline()
            exe = p.exe().replace('\\', '/').lower()
            server = ('/.minecraft/runtime/' in exe and
                      '-jar' in args and args[args.index('-jar')+1:] == ['server.jar', 'nogui'])
            if server:
                cpu = p.cpu_times()
                background.append(dict(item, executable=exe, args=args,
                                       cpu_seconds=cpu.user+cpu.system,
                                       rss=p.memory_info().rss,
                                       reason='Minecraft server, not Flex/FFDec compilation'))
            else:
                blockers.append(dict(item, args=args))
        except psutil.NoSuchProcess:
            continue
        except (psutil.AccessDenied, IndexError):
            blockers.append(item)
    env['processes'] = blockers
    env['background_java'] = background
    return env
