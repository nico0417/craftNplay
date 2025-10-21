import os
import json
from discord.ext import commands

class Installer(commands.Cog):
    """
    Cog para instalar y registrar nuevos servidores de Minecraft.
    """
    def __init__(self, bot):
        self.bot = bot
        # Usar el manager central en lugar de manejar el archivo localmente
        self.config = getattr(bot, "config_manager", None)
        if self.config is None:
            # Fallback por si el bot no tiene config_manager
            self.servers_file = 'servers.json'
        else:
            self.servers_file = self.config.servers_file

    def load_servers(self):
        """Carga la base de datos de servidores de forma segura."""
        if not os.path.exists(self.servers_file):
            return {}
        try:
            with open(self.servers_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_servers(self, data):
        """Guarda los datos en la base de datos de servidores."""
        with open(self.servers_file, 'w') as f:
            json.dump(data, f, indent=4)

    @commands.command(name='install')
    @commands.is_owner()
    async def install_server(self, ctx, server_type: str, version: str, base_name: str, *, parent_path: str):
        """
        Crea la estructura de carpetas para un nuevo servidor y lo registra.
        Uso: !install <tipo> <version> <nombre> <ruta_padre>
        Ejemplo: !install neoforge 1.21.1 mi_servidor D:\\ServidoresMC
        """
        # 1. Validar que la ruta padre exista
        if not os.path.isdir(parent_path):
            await ctx.send(f'❌ La ruta padre `{parent_path}` no existe o no es un directorio.')
            return

        # 2. Crear la ruta completa y la carpeta del servidor
        folder_name = f"{base_name}_{version}_{server_type}"
        full_server_path = os.path.join(parent_path, folder_name)

        if os.path.exists(full_server_path):
            await ctx.send(f'⚠️ La carpeta `{full_server_path}` ya existe. No se ha realizado ninguna acción.')
            return

        try:
            os.makedirs(full_server_path)
            await ctx.send(f'✅ Carpeta del servidor creada en: `{full_server_path}`')
        except OSError as e:
            await ctx.send(f'❌ Error al crear la carpeta del servidor: {e}')
            return

        # 3. Registrar el nuevo servidor en servers.json
        # Usar el manager centralizado
        if self.config:
            if base_name in self.config.servers:
                await ctx.send(f'⚠️ Ya existe una configuración para un servidor llamado `{base_name}`. Se sobrescribirá.')
            self.config.servers[base_name] = {
                "path": full_server_path,
                "script": "run.bat",
                "address": "localhost:25565",
                "rcon_port": 25575,
                "rcon_host": "localhost"
            }
            self.config.save_servers()
        else:
            servers = self.load_servers()
            if base_name in servers:
                await ctx.send(f'⚠️ Ya existe una configuración para un servidor llamado `{base_name}`. Se sobrescribirá.')
            servers[base_name] = {
                "path": full_server_path,
                "script": "run.bat",
                "address": "localhost:25565",
                "rcon_port": 25575,
                "rcon_host": "localhost"
            }
            self.save_servers(servers)

        await ctx.send(f'💾 ¡Servidor `{base_name}` registrado en `servers.json`! Ahora puedes usar `!iniciar {base_name}`.')
        
        # Simulación de los siguientes pasos
        await ctx.send(f'**Próximos pasos (manuales):**\n'
                       f'1. Descarga el instalador de `{server_type}` para la versión `{version}`.\n'
                       f'2. Ejecútalo dentro de la nueva carpeta para instalar los archivos del servidor.\n'
                       f'3. Asegúrate de que el script de inicio se llame `run.bat` o actualiza `servers.json` con el nombre correcto.')

    @install_server.error
    async def install_error(self, ctx, error):
        """Manejo de errores para el comando de instalación."""
        if isinstance(error, commands.NotOwner):
            await ctx.send('❌ Este comando solo puede ser usado por el dueño del bot.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'❌ Faltan argumentos. Uso correcto: `!install <tipo> <version> <nombre> <ruta_padre>`')
        else:
            await ctx.send(f'Ocurrió un error inesperado: {error}')

async def setup(bot):
    """Función para cargar el Cog en el bot."""
    await bot.add_cog(Installer(bot))