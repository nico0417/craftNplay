# Importa las librerías necesarias
import discord
from discord.ext import commands
import subprocess
import os
import signal
import asyncio
from mcstatus import JavaServer
from mcrcon import MCRcon

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

if TOKEN is None:
    print("Error: No se encontró el token del bot en la variable de entorno 'DISCORD_BOT_TOKEN'")
    exit()
if RCON_PASSWORD is None:
    print("Advertencia: No se encontró la contraseña RCON. Los comandos !detener y !reiniciar no funcionarán de forma segura.")

BASE_PATH = 'C:/Users/Nicolas/Documents/Fabric'
SCRIPT_PATH = os.path.join(BASE_PATH, 'start.bat')
SERVER_DIRECTORY = BASE_PATH
# Ruta directa al ejecutable de Playit
PLAYIT_PATH = 'C:/Program Files/playit_gg/bin/playit.exe'

MINECRAFT_SERVER_ADDRESS = "localhost:25565"
RCON_PORT = 25575
RCON_HOST = "localhost"

# --- VARIABLES GLOBALES ---
# Ahora guardamos el proceso del servidor Y el de playit
server_process = None
playit_process = None

# --- CÓDIGO DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNCIONES AUXILIARES MEJORADAS ---

async def start_server(ctx):
    """Inicia Playit y el servidor de Minecraft."""
    global server_process, playit_process

    if server_process is not None and server_process.poll() is None:
        await ctx.send('⚠️ ¡El servidor ya está en funcionamiento!')
        return False

    await ctx.send('✅ Iniciando servicios... ¡Un momento!')
    try:
        # 1. Iniciar Playit.exe
        if playit_process is None or playit_process.poll() is not None:
            print("Iniciando Playit.gg...")
            playit_process = subprocess.Popen(PLAYIT_PATH)
            await ctx.send(' tunneling de Playit.gg iniciado.')
            await asyncio.sleep(10) # Darle tiempo a Playit para establecer la conexión
        else:
            await ctx.send(' tunneling de Playit.gg ya estaba activo.')

        # 2. Iniciar el servidor de Minecraft
        print("Iniciando el servidor de Minecraft...")
        server_process = subprocess.Popen(
            SCRIPT_PATH,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=SERVER_DIRECTORY
        )
        print(f'Servidor iniciado con PID: {server_process.pid}')
        await ctx.send('Servidor de Minecraft iniciado. Debería estar en línea en unos minutos.')
        return True
    except Exception as e:
        await ctx.send(f'❌ Hubo un error al iniciar los servicios: {e}')
        return False

async def stop_server(ctx, stop_playit: bool):
    """Detiene el servidor y, opcionalmente, Playit."""
    global server_process, playit_process

    if server_process is None or server_process.poll() is not None:
        await ctx.send('⚠️ ¡El servidor no está en funcionamiento!')
        return False

    await ctx.send('⛔ Intentando un cierre seguro del servidor...')
    
    stopped_safely = False
    # Fase 1: Intentar cierre seguro con RCON
    if RCON_PASSWORD:
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command("stop")
            await ctx.send('Comando "stop" enviado. Esperando a que el servidor cierre...')
            # Esperar a que el proceso termine por su cuenta
            await asyncio.to_thread(server_process.wait, timeout=30)
            stopped_safely = True
        except Exception as rcon_e:
            await ctx.send(f'⚠️ No se pudo conectar con RCON para un cierre seguro ({rcon_e}). Procediendo a forzar el cierre.')
    
    # Fase 2: Forzar el cierre si es necesario
    if not stopped_safely:
        await ctx.send('El servidor no respondió. Forzando el cierre...')
        try:
            # Usamos taskkill, que es mucho más efectivo para cerrar procesos y sus hijos
            os.system(f"taskkill /F /T /PID {server_process.pid}")
        except Exception as kill_e:
            await ctx.send(f'❌ Error al forzar el cierre: {kill_e}')
            return False

    server_process = None
    await ctx.send('✅ ¡Servidor de Minecraft detenido!')

    # Lógica para detener Playit solo si es necesario
    if stop_playit:
        if playit_process and playit_process.poll() is None:
            await ctx.send('Cerrando el túnel de Playit.gg...')
            playit_process.kill()
            playit_process = None
            await ctx.send('Túnel de Playit.gg cerrado.')
    
    return True


# --- EVENTOS Y COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    print('Comandos: !iniciar, !detener, !reiniciar, !status')

@bot.command(name='iniciar', aliases=['start'])
async def iniciar_command(ctx):
    """Inicia Playit y el servidor de Minecraft."""
    await start_server(ctx)

@bot.command(name='detener', aliases=['stop'])
async def detener_command(ctx):
    """Detiene el servidor de Minecraft y Playit."""
    # Le pasamos stop_playit=True para que también cierre Playit
    await stop_server(ctx, stop_playit=True)

@bot.command(name='reiniciar', aliases=['restart'])
async def reiniciar_command(ctx):
    """Reinicia el servidor de Minecraft, manteniendo Playit activo."""
    await ctx.send('🔄 Reiniciando el servidor...')
    # Le pasamos stop_playit=False para que NO cierre Playit
    if await stop_server(ctx, stop_playit=False):
        await ctx.send('Servidor detenido, iniciando de nuevo en 5 segundos...')
        await asyncio.sleep(5)
        await start_server(ctx)

@bot.command(name='status')
async def status_command(ctx):
    """Consulta el estado del servidor de Minecraft."""
    await ctx.send("🔍 Consultando el estado del servidor...")
    try:
        # 1. Usar mcstatus para obtener información general (ping, versión, etc.)
        server = await JavaServer.async_lookup(MINECRAFT_SERVER_ADDRESS)
        status = await server.async_status()
        
        embed = discord.Embed(
            title="✅ Servidor En Línea",
            description=f"El servidor está funcionando correctamente.",
            color=discord.Color.green()
        )
        embed.add_field(name="Versión", value=status.version.name, inline=True)
        embed.add_field(name="Jugadores", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="Latencia", value=f"{status.latency:.2f} ms", inline=True)
        
        # 2. Usar RCON para obtener una lista de jugadores fiable
        if status.players.online > 0 and RCON_PASSWORD:
            try:
                # Usamos un executor para no bloquear el bot con la conexión RCON
                def get_player_list():
                    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                        resp = mcr.command("/list")
                        players_line = None
                        # El formato es "There are 1/20 players online:\nPlayer1, Player2"
                        if ":" in resp and "\n" in resp:
                            players_line = resp.split(':\n', 1)[1]
                        elif ":" in resp:
                             players_line = resp.split(': ', 1)[1]
                        
                        if players_line:
                            # Separamos los nombres por la coma y eliminamos espacios
                            player_names = [name.strip() for name in players_line.split(',')]
                            # Unimos los nombres con un salto de línea para la lista vertical
                            return "\n".join(player_names)
                        
                        return None

                player_list = await asyncio.to_thread(get_player_list)

                if player_list:
                    embed.add_field(name=f"Jugadores Conectados ({status.players.online})", value=f"```{player_list}```", inline=False)
                else:
                    # Si RCON no devuelve jugadores pero el ping sí, mostramos un mensaje genérico
                    embed.add_field(name=f"Jugadores Conectados ({status.players.online})", value="Hay jugadores en el servidor.", inline=False)

            except Exception as rcon_e:
                print(f"Error al conectar con RCON: {rcon_e}")
                embed.add_field(name="Jugadores Conectados", value="No se pudo obtener la lista (error de RCON).", inline=False)
                embed.set_footer(text="Verifica que RCON esté bien configurado en server.properties y la contraseña sea correcta.")

        await ctx.send(embed=embed)

    except Exception as e:
        print(f"Error al consultar el estado del servidor: {e}")
        embed = discord.Embed(
            title="❌ Servidor Fuera de Línea",
            description="No se pudo conectar con el servidor. Puede que esté apagado o iniciándose.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Inicia el bot
bot.run(TOKEN)