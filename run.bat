IF NOT EXIST env (
    python -m venv env
    call env\Scripts\activate
    pip install -r requirements.txt --proxy=10.190.10.145:80
) ELSE (
    call env\Scripts\activate
)
python FreeReq.py
