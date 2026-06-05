import subprocess


def get_latest_commit() -> dict:
    try:
        result = subprocess.run(
            ["git", "log", "-1", '--pretty=format:"%h|%s|%cr"'],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        output = result.stdout.strip().strip('"')
        if not output:
            return {"hash": "", "description": "", "time": ""}

        commit_hash, description, time = output.split("|", 2)
        return {
            "hash": commit_hash,
            "description": description,
            "time": time
        }
    except (ValueError, subprocess.SubprocessError):
        return {"hash": "", "description": "", "time": ""}
