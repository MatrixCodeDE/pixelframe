<div style="display: flex; align-items: center;">
    <img src="https://raw.githubusercontent.com/MatrixCodeDE/pixelframe/main/Misc/icon.svg" width="100" alt="PixelFrame" title="PixelFrame by Matrix">
    <div style="margin-left: 20px; display: flex; align-items: center;">
        <h1 style="margin: 0;">PixelFrame: Multiplayer canvas</h1>
    </div>
</div>

## r/Place for hackers and computer scientists

#### Pixelframe is a rewrite of the [Pixelflut Project](https://github.com/defnull/pixelflut), compatible with Python 3.

I wanted to use the Pixelflut project for a university project, but I found out that it was written in Python 2, which is heavily outdated, so I created this.

<h1>Features</h1>

Since this is a rewrite of the entire original project, I also added some features the old one has not.
## ⚡️ Fast Base
Based on numpy, the new heart of the canvas is almost **6x faster&#42;** than the old version. It is also very efficient in performing actions on large data like a picture with metadata for every pixel.

> &#42;Based on calculations

## 🖼 Webinterface

Shows the canvas in a browser
Can display the current canvas, also featuring the integrated Documentation on /docs and /redoc

## 🖥 Local Display

Displays the canvas on a local display connected to the host. \
PyGame isn't exactly a new feature, but its optional now. Also, you can display a stats bar for connection details and basic stats of the canvas when using in public.

> Note: this feature requires a host with graphic drivers, e.g. Docker containers won't work!

## 📟 API

Based on FastAPI, can update pixels and also hosting the [Webinterface](#-webinterface) \
Usage [Coming Soon]

## 🔌 Interactive Sockets

Like the old version, this project uses sockets to communicate with the players. You can set pixels, get pixel colors and even view stats for the whole canvas. New features are a timeout for the connection and a cooldown for spam protection.

## ⚙️ Config

A config for creating templates and sharing them, made easy.
<details>
<summary>Options</summary>

- Name
- Game Rules
- Frontends Settings
- Connection Infos
- Canvas Settings
</details>

# Server
## Installation

```shell
cd pixelframe
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Configuration
<details>
<summary>Server</summary>
Take a look at the [config file]()
</details>

<details>
<summary>Certificates (HTTPS)</summary>
PixelFrame supports Certificates natively (modify via Uvicorn), but I highly recommend nginx.
If you want to install PixelFrame on a server with nginx and Certificates to enable encryption for the API with HTTPS you have to make sure you don't overlap any ports.
Use port `8443` (or any port with X443) for the API since other ports won't accept encryption. But I recommend to use port `8000` for the base of the API and then map `8080` (HTTP) and/or `8443` (HTTPS) to the base. 
</details>


### Starting

```shell
python3 [-c configfile] pixelframe.py
```

### Contribution

If you want to improve this repository, feel free to contribute. \
Please install `dev-requirement.txt`, comment your changes properly and run the following script before committing:

```shell
python3 -m black .
python3 -m isort .
```

## Credits

* [Pixelflut](https://github.com/defnull/pixelflut) - A lot of inspiration and code snippets
* [Leon](https://git.leon.wtf/leon/pixelflut) - The `STATS` command
* [LyonsType](./Misc/OFL.txt) - The font `LT Superior Mono`

## Disclaimer   

> Most of the HTML and JS code if very sketchy and copied together from diverse websites, so there might be some bugs here and there. Contribute if you want to improve it, I'd appreciate it very much!
> PixelFrame currently uses Greenlets to work with pygame threads. This messes the whole code up by a lot, I might remove pygame in the future to work with asyncio.
