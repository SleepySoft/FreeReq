IF NOT EXIST env (
    python -m venv env
    call env\Scripts\activate
    pip install -r requirements.txt
) ELSE (
    call env\Scripts\activate
)
python FreeReq.py
