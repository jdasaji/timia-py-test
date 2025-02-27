import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError

aws_region = "us-east-1"
name_bucket = "py-test--use1-az6--x-s3"


def get_secret():
    secret_name = "dev/py/test-file"
    region_name = "us-east-1"

    # Crear el cliente de AWS Secrets Manager
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        # Si el secreto está en formato JSON, lo convertimos en un diccionario
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])

    except ClientError as e:
        print(f"Error al obtener el secreto: {e}")
        return None  # Devuelve None si hay un error


def lambda_handler(event, context):
    modelSecrect = get_secret()

    print("Iniciando lambda_handler")  # Debug inicial

    if not modelSecrect:
        raise ValueError("No se pudieron obtener las credenciales de AWS.")

    aws_access_key_id = modelSecrect.get("key-s3")
    aws_secret_access_key = modelSecrect.get("secrect-s3")

    if not aws_access_key_id or not aws_secret_access_key:
        raise ValueError("Las credenciales recuperadas son inválidas.")

    print(f"Usando AWS Access Key ID: {aws_access_key_id}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"hola_{timestamp}.txt"
    file_content = "Hola"

    # Crear archivo temporal en /tmp/--solo para lambda
    file_path = f"/tmp/{file_name}"
    with open(file_path, "w") as f:
        f.write(file_content)

    #test
    # Crear cliente de S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

    # Subir archivo a S3
    try:
        s3.upload_file(file_path, name_bucket, file_name)
        print(f"El archivo '{file_name}' se subió correctamente al bucket '{name_bucket}'.")
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
        return {
            "statusCode": 500,
            "body": f"Error al subir el archivo: {str(e)}"
        }
    finally:
        # Eliminar el archivo local en /tmp/
        os.remove(file_path)

    return {
        "statusCode": 200,
        "body": f"Archivo '{file_name}' subido a S3 exitosamente."
    }

