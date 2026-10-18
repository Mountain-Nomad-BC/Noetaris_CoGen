"""Create random local Docker Compose secrets, without printing their values."""
from pathlib import Path
import os
import secrets

def main():
    root = Path(__file__).resolve().parents[1] / "secrets"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name in ("api_token", "db_password", "app_db_password", "admin_token", "reviewer_token", "viewer_token", "parser_token", "model_token", "ocr_token", "encoder_token", "redis_password", "oauth_cookie_signing"):
        path = root / f"{name}.txt"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if name == 'model_token':
                # C++ getline keeps CR from Windows CRLF; preserve key value but use LF wire format.
                data=path.read_bytes()
                if b'\r\n' in data:
                    path.write_bytes(data.replace(b'\r\n',b'\n'))
            print(f"{name}: exists, unchanged")
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(secrets.token_urlsafe(48) + "\n")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        print(f"{name}: created")


if __name__ == "__main__":
    main()
