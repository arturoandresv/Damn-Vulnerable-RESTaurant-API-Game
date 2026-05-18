import subprocess

ALLOWED_DF_ARGS = {"-h", "-T", "-a", "--total"}

def get_disk_usage(parameters: str):
    
    safe_args = [arg for arg in parameters.split() if arg in ALLOWED_DF_ARGS]
    
    command = ["df"] + safe_args

    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        usage = result.stdout.strip().decode()
    except:
        raise Exception("An unexpected error was observed")

    return usage
