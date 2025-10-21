# Bot de Gestión para Servidor de Minecraft

Un bot de Discord simple pero potente escrito en Python para gestionar un servidor de Minecraft (incluyendo NeoForge/Fabric) de forma remota. Permite iniciar, detener, reiniciar y comprobar el estado del servidor, incluyendo el túnel de Playit.gg.

## 🎮 Funcionalidades Principales

* **!iniciar**: Inicia `playit.exe` y el servidor de Minecraft.
* **!detener**: Envía un comando `stop` seguro (vía RCON) al servidor y cierra tanto el servidor como `playit.exe`.
* **!reiniciar**: Reinicia el servidor de forma segura sin interrumpir el túnel de `playit.gg`.
* **!estado**: Muestra un Embed de Discord con el estado del servidor, incluyendo versión, ping y la lista de jugadores conectados (obtenida por RCON para compatibilidad con modo no-premium).

## 🚀 Cómo Funciona

El bot utiliza `discord.py` para la interfaz de Discord y `mcstatus` para las comprobaciones de estado. Para un control robusto, utiliza `mcrcon` para enviar comandos de apagado seguro directamente a la consola del servidor. La gestión de los procesos (servidor y Playit) se maneja con el módulo `subprocess` de Python, permitiendo un control total sobre el inicio y cierre de cada aplicación.

## 🛠️ Instalación y Configuración

1.  **Clonar el Repositorio:**
    ```sh
    git clone [https://github.com/TuUsuario/minecraft-discord-bot.git](https://github.com/TuUsuario/minecraft-discord-bot.git)
    cd minecraft-discord-bot
    ```

2.  **Instalar Dependencias:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Configurar el Servidor de Minecraft:**
    * Asegúrate de tener un servidor de Minecraft (Vanilla, Fabric, NeoForge) en una carpeta.
    * En el archivo `server.properties` del servidor, habilita RCON:
        ```properties
        enable-rcon=true
        rcon.port=25575
        rcon.password=TuContraseñaSeguraRCON
        ```

4.  **Configurar las Variables de Entorno:**
    El bot carga las credenciales de forma segura. Debes configurar las siguientes variables de entorno en tu sistema:
    * `DISCORD_BOT_TOKEN`: El token secreto de tu bot de Discord.
    * `RCON_PASSWORD`: La contraseña que acabas de poner en `server.properties`.

5.  **Actualizar las Rutas:**
    * Dentro de `bot.py`, ajusta las siguientes variables en la sección de configuración para que coincidan con tus rutas locales:
        ```python
        BASE_PATH = 'C:/Ruta/A/Tu/Servidor'
        PLAYIT_PATH = 'C:/Ruta/A/playit.exe'
        ```

6.  **Ejecutar el Bot:**
    ```sh
    python bot.py
    ```

---

*Este proyecto fue creado como una herramienta de gestión personal para un servidor de amigos.*