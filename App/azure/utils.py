import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, assume env vars are set

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)


def is_link(string):
    """
    Verifica se uma string é um URL válido
    """
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# Configuração do Azure Blob Storage
AZURE_ACCOUNT_NAME = os.getenv('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_ACCOUNT_KEY')


if AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY:
    blob_service_client = BlobServiceClient(
        account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_ACCOUNT_KEY
    )
else:
    blob_service_client = None


async def upload_file(file_buffer, blob_name, container_name):
    """
    Faz upload de um ficheiro para o Azure Blob Storage
    
    Args:
        file_buffer: Buffer do ficheiro (bytes)
        blob_name: Nome do blob
        container_name: Nome do container
        
    Returns:
        URL do blob
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        upload_response = blob_client.upload_blob(
            file_buffer,
            overwrite=True
        )
        
        return blob_client.url
        
    except Exception as error:
        print(str(error))
        raise


async def update_file(
    file,
    container,
    existing_blob=None,
    allowed_file_extensions=None
):
    """
    Atualiza um ficheiro no Azure Blob Storage
    
    Args:
        file: Objeto de ficheiro Django (UploadedFile)
        container: Nome do container
        existing_blob: Nome do blob existente (opcional)
        allowed_file_extensions: Lista de extensões permitidas (opcional)
        
    Returns:
        URL do blob no Azure Storage
    """
    if not file or not hasattr(file, 'read') or not hasattr(file, 'name'):
        raise ValueError('Invalid file object')
    
    try:
        # Apagar ficheiro existente se fornecido
        if existing_blob is not None:
            try:
                await delete_file(existing_blob, container)
            except Exception as error:
                raise
        
        # Ler o conteúdo do ficheiro
        file_buffer = file.read()
        original_filename = file.name
        file_extension = Path(original_filename).suffix.lower()
        
        # Validar extensão do ficheiro
        if (allowed_file_extensions is not None and 
            file_extension not in allowed_file_extensions):
            raise ValueError(
                f'Profile Pic must be one of the following: {", ".join(allowed_file_extensions)}'
            )
        
        # Gerar nome aleatório para o blob
        blob_name = secrets.token_hex(8) + file_extension

        if(existing_blob):
            blob_name = existing_blob
        
        try:
            url = await upload_file(file_buffer, blob_name, container)
        except Exception as error:
            raise
        
        return url
        
    except Exception as error:
        print(str(error))
        raise


def generate_sas_url(blob_name_or_url, container_name):
    """
    Gera um URL SAS temporário para um blob
    
    Args:
        blob_name_or_url: Nome do blob ou URL completa do blob
        container_name: Nome do container
        
    Returns:
        URL com token SAS
    """
    # Se for uma URL, extrair o blob_name
    if blob_name_or_url.startswith('https://') and '.blob.core.windows.net' in blob_name_or_url:
        # URL format: https://account.blob.core.windows.net/container/blobname
        parts = blob_name_or_url.split('/')
        blob_name = '/'.join(parts[5:])  # blobname pode ter /
    else:
        blob_name = blob_name_or_url
    
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    # Definir permissões (apenas leitura)
    permissions = BlobSasPermissions(read=True)
    
    # Definir tempo de expiração (1 hora)
    expiry_time = datetime.utcnow() + timedelta(hours=1)
    
    # Gerar token SAS
    sas_token = generate_blob_sas(
        account_name=AZURE_ACCOUNT_NAME,
        container_name=container_name,
        blob_name=blob_name,
        account_key=AZURE_ACCOUNT_KEY,
        permission=permissions,
        expiry=expiry_time
    )
    
    sas_url = f"{blob_client.url}?{sas_token}"
    return sas_url


async def delete_file(blob_name_or_url, container_name):
    """
    Elimina um ficheiro do Azure Blob Storage
    
    Args:
        blob_name_or_url: Nome do blob ou URL completa do blob
        container_name: Nome do container
    """
    # Se for uma URL, extrair o blob_name
    if blob_name_or_url.startswith('https://') and '.blob.core.windows.net' in blob_name_or_url:
        # URL format: https://account.blob.core.windows.net/container/blobname
        parts = blob_name_or_url.split('/')
        blob_name = '/'.join(parts[5:])  # blobname pode ter /
    else:
        blob_name = blob_name_or_url
    
    try:
        
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        delete_response = blob_client.delete_blob(delete_snapshots='include')
        
        
    except Exception as error:
        raise
