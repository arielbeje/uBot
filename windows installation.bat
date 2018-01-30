echo creating virtual environment
python -m venv uBot-env 2>NUL || python3 -m venv uBot-env
CALL uBot-env\Scripts\activate.bat
echo virtual environment created and activated. installing discord.py rewrite
python -m pip install -U git+https://github.com/Rapptz/discord.py@rewrite 2>NUL || python3 -m pip install -U git+https://github.com/Rapptz/discord.py@rewrite
echo discord.py installed. installing pip packages.
pip install -r reqs.txt
echo all done