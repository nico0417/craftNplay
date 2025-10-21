from discord.ext import commands
import os
import json
import asyncio
import subprocess
from mcrcon import MCRcon

# Rol requerido para usar estos comandos
ADMIN_ROLE = "Admin" 

class ServerManagement(commands.Cog):
    """
    Cog para la gestión de los servidores de Minecraft (iniciar, detener, reiniciar).
    """
    def __init__(self, bot):
        self.bot = bot
        # Diccionario para rastrear los procesos de los servidores en ejecución
        self.running_servers = {}
        # Cargar la contraseña RCON global desde el entorno para el cierre seguro
        self.rcon_password = os.getenv('RCON_PASSWORD')
        # Usar el manager central en vez de leer el JSON cada vez
        self.config = getattr(bot, "config_manager", None)

    def load_server_data(self):
        """Carga la base de datos de servidores desde servers.json."""
        if self.config:
            return self.config.servers
        try:
            with open('servers.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @commands.command(name='iniciar')
    @commands.has_role(ADMIN_ROLE)
    async def start_server(self, ctx, server_name: str):
        """Inicia un servidor de Minecraft especificado por su nombre."""
        if server_name in self.running_servers and self.running_servers[server_name].poll() is None:
            await ctx.send(f'⚠️ ¡El servidor `{server_name}` ya está en funcionamiento!')
            return

        servers_data = self.load_server_data()
        server_info = servers_data.get(server_name)

        if not server_info:
            await ctx.send(f'❌ No se encontró ningún servidor con el nombre `{server_name}` en `servers.json`.')
            return

        server_path = server_info.get('path')
        script_name = server_info.get('script', 'start.bat') # Usa start.bat por defecto
        script_path = os.path.join(server_path, script_name)

        if not os.path.exists(script_path):
            await ctx.send(f'❌ El script de inicio `{script_path}` no existe.')
            return

        try:
            await ctx.send(f'✅ Iniciando el servidor `{server_name}`...')
            process = subprocess.Popen(
                script_path,
                cwd=server_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.running_servers[server_name] = process
            await ctx.send(f'El servidor `{server_name}` se ha iniciado con PID: `{process.pid}`. Dale unos minutos para que esté en línea.')
        except Exception as e:
            await ctx.send(f'❌ Ocurrió un error inesperado al iniciar `{server_name}`: {e}')

    @commands.command(name='detener')
    @commands.has_role(ADMIN_ROLE)
    async def stop_server(self, ctx, server_name: str):
        """Detiene un servidor de Minecraft en ejecución."""
        if server_name not in self.running_servers or self.running_servers[server_name].poll() is not None:
            await ctx.send(f'⚠️ El servidor `{server_name}` no está en funcionamiento.')
            return

        process = self.running_servers[server_name]
        servers_data = self.load_server_data()
        server_info = servers_data.get(server_name, {})
        
        rcon_port = server_info.get('rcon_port', 25575)
        rcon_host = server_info.get('rcon_host', 'localhost')

        stopped_safely = False
        if self.rcon_password:
            await ctx.send(f'⛔ Intentando un cierre seguro de `{server_name}` vía RCON...')
            try:
                with MCRcon(rcon_host, self.rcon_password, port=rcon_port) as mcr:
                    mcr.command("stop")
                await ctx.send('Comando "stop" enviado. Esperando 30 segundos para el cierre...')
                await asyncio.to_thread(process.wait, timeout=30)
                stopped_safely = True
                await ctx.send(f'✅ El servidor `{server_name}` se ha detenido de forma segura.')
            except Exception as e:
                await ctx.send(f'⚠️ No se pudo usar RCON ({e}). Forzando el cierre.')
        
        if not stopped_safely:
            await ctx.send(f'Forzando el cierre del proceso PID: `{process.pid}`...')
            try:
                os.system(f"taskkill /F /T /PID {process.pid}")
                await ctx.send(f'✅ El servidor `{server_name}` ha sido forzado a detenerse.')
            except Exception as e:
                await ctx.send(f'❌ Error al forzar el cierre: {e}')
                return

        # Limpiar el diccionario
        del self.running_servers[server_name]

    @commands.command(name='reiniciar')
    @commands.has_role(ADMIN_ROLE)
    async def restart_server(self, ctx, server_name: str):
        """Reinicia un servidor de Minecraft."""
        await ctx.send(f'🔄 Reiniciando el servidor `{server_name}`...')
        
        # Primero, intenta detener el servidor. El comando stop_server ya maneja los mensajes.
        await self.stop_server(ctx, server_name)
        await asyncio.sleep(5)  # Esperar un momento antes de iniciar de nuevo
        await self.start_server(ctx, server_name)

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))