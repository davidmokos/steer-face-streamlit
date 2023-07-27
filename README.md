## How to run

1. create a file `.streamlit/secrets.toml` with content:

```
[firebase]
credentials = """
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "...",
  ...
}
"""
```

2. `pip install -r requirements.py`
3. `streamlit run app.py`