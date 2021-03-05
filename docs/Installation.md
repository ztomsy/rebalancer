# Installation

This page explains how to prepare your environment for running the bot.

## Prerequisite

Before running your bot in production you will need to setup few
external API. In production mode, the bot will require valid Exchange API
credentials. 

### Setup your exchange account

You will need to create API Keys (Usually you get `key` and `secret`) from the Exchange website and insert this into the appropriate fields in the configuration or when asked by the installation script.

## Quick start

```bash
git clone git@github.com:ztomsy/rebalancer.git
cd rebalancer
python -m pip install requirements
cp _setings.py settings.py
```
Modify your settings and run it in various ways:
```bash
python run.py
```
or run new tmux session with script and settings file in nano
```bash
sh start.sh
```

Windows and MacOS installation explanation required!

------

## Custom Installation

We've included/collected install instructions for Ubuntu. These are guidelines and your success may vary with other distros.
OS Specific steps are listed first, tthe [Common](#common) section below is necessary for all systems.

### Requirements

Click each one for install guide:

* [Python >= 3.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)

### Linux - Ubuntu

#### Install Python 3.7, Git, and wget

```bash
sudo add-apt-repository ppa:jonathonf/python-3.7
sudo apt-get update
sudo apt-get install python3.7 python3.7-venv python3.7-dev build-essential autoconf libtool pkg-config make wget git
```

#### Raspberry Pi / Raspbian

Before installing on a Raspberry Pi running the official Raspbian Image, make sure you have at least Python 3.7 installed. The default image only provides Python 3.5. Probably the easiest way to get a recent version of python is [miniconda](https://repo.continuum.io/miniconda/).

The following assumes that miniconda3 is installed and available in your environment. Last miniconda3 installation file use python 3.4, we will update to python 3.6 on this installation.
It's recommended to use (mini)conda for this as installation/compilation of `numpy`, `scipy` and `pandas` takes a long time.

Additional package to install on your Raspbian, `libffi-dev` required by cryptography (from python-telegram-bot).

``` bash
conda config --add channels rpi
conda install python=3.7
conda create -n rebalancer python=3.7
conda activate rebalancer

sudo apt install libffi-dev
python3.7 -m pip install -r requirements.txt
python3.7 -m pip install -e .
```

### MacOS

#### Install Python 3.7, git and wget

```bash
brew install python3 git wget
```

### Windows

#### Install dependecies and clone the bot

### Common

#### 2. Setup your Python virtual environment (virtualenv)

!!! Note
    This step is optional but strongly recommended to keep your system organized

```bash
python3 -m venv venv
source venv/bin/activate
```
or if you use fish
```bash
source venv/bin/activate.fish 

```

#### 3. Install ReBalancer

Clone the git repository:

```bash
git clone git@github.com:ztomsy/rebalancer.git
```

Optionally checkout the stable/master branch:

```bash
git checkout master
```

#### 4. Initialize the configuration

```bash
cd rebalancer
cp _setings.py settings.py
```

> *To edit the config please refer to [Bot Configuration](Configuration.md).*

#### 5. Install python dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### 6. Run the Bot

If this is the first time you run the bot, ensure you are running it in Dry-run `"dry_run": true,` otherwise it will start to buy and sell coins.

```bash
python run.py
```

*Note*: If you run the bot on a server, you should consider using Docker or a terminal multiplexer like [`tmux`](https://en.wikipedia.org/wiki/Tmux) to avoid that the bot is stopped on logout.

---

Now you have an environment ready, the next step is
[Bot Configuration](Configuration.md).