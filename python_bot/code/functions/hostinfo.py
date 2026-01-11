import psutil

def get_formatted_ram_usage():
    mem = psutil.virtual_memory()
    used_gb = mem.used / 1024 / 1024 / 1024
    total_gb = mem.total / 1024 / 1024 / 1024
    percent = mem.percent
    return f"<:ram:1363597677912264966> | RAM: **{used_gb:.1f} / {total_gb:.1f} GB ({percent}%)**"

def get_formatted_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)

    cpu_temp = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            cpu_temp = int(temp_str) / 1000  
    except FileNotFoundError:
        pass  

    if cpu_temp is not None:
        return f"<:cpu:1363599094395834430> | CPU: **{cpu_percent}% @ {cpu_temp:.1f}°C**"
    else:
        return f"<:cpu:1363599094395834430> | CPU: **{cpu_percent}%**"

def get_formatted_storage_usage():
    disk = psutil.disk_usage('/')
    used_gb = disk.used / 1024 / 1024 / 1024
    total_gb = disk.total / 1024 / 1024 / 1024
    return f"<:ssd:1363600388959506585> | Storage: **{used_gb:.1f} / {total_gb:.1f} GB**"

def get_command_counts(bot):
    pc = {c.qualified_name for c in bot.commands}
    sc = set()

    def collect(cmds):
        for c in cmds:
            sc.add(c.qualified_name)
            if hasattr(c, "commands"):
                collect(c.commands)

    collect(bot.tree.get_commands())
    return len(pc | sc), len(pc), len(sc)