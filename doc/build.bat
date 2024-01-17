python -m venv pack
call pack\Scripts\activate
pip install -r requirements.txt --proxy=10.190.10.145:80
pyinstaller.exe -D -i doc/logo.ico --add-data "FreeReq.req;." --add-data "res;res" --add-data "README.md;." FreeReq.py
