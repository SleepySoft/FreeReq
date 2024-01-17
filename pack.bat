IF NOT EXIST env (
    python -m venv env
    call env\Scripts\activate
    pip install -r requirements.txt
) ELSE (
    call env\Scripts\activate
)
pyinstaller.exe -D -i doc/logo.ico --add-data "FreeReq.req;." --add-data "res;res" --add-data "README.md;." FreeReq.py
