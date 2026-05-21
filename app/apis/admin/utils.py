import subprocess

#Definir una lista de parametros de df permitidos
ALLOWED_DF_ARGS = {"-h","-T","-a","--total"}

def get_disk_usage(parameters: str):
    
    #Permite solo los parametros dentro de la lista
    safe_args = [arg for arg in parameters.split() if arg in ALLOWED_DF_ARGS]
    
    #Construye el comando mediante una lista
    command = "df" + safe_args

    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        usage = result.stdout.strip().decode()
    except:
        raise Exception("An unexpected error was observed")

    return usage

