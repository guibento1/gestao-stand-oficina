import pytest
import os
from django.db import connection
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Carrega schema de teste de ficheiro SQL"""
    with django_db_blocker.unblock():
        with connection.cursor() as cur:
            # Caminho para o ficheiro SQL
            sql_file = os.path.join(
                os.path.dirname(__file__),  # Pasta onde está o conftest.py
                'test_schema_setup.sql'
            )
            
            print(f"Carregando SQL de: {sql_file}")
            
            # Ler e executar o ficheiro SQL
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cur.execute(sql_script)
            
            connection.connection.commit()
            print("Schema de teste configurado com sucesso")
    
    yield

@pytest.fixture
def test_db_cursor(django_db_blocker):
    """Fornece cursor para os testes"""
    with django_db_blocker.unblock():
        cur = connection.cursor()
        try:
            yield cur
        finally:
            try:
                connection.connection.commit()
            except Exception:
                connection.connection.rollback()

@pytest.fixture(autouse=True)
def cleanup_test_data(django_db_blocker):
    """Limpa dados após cada teste"""
    yield
    
    with django_db_blocker.unblock():
        try:
            with connection.cursor() as cur:
                # Limpar na ordem correta (por causa das foreign keys)
                cur.execute("TRUNCATE TABLE test_schema.vendas CASCADE;")
                cur.execute("TRUNCATE TABLE test_schema.carros CASCADE;")
                cur.execute("TRUNCATE TABLE test_schema.clientes CASCADE;")
                cur.execute("TRUNCATE TABLE test_schema.stands CASCADE;")
                cur.execute("TRUNCATE TABLE test_schema.marcas CASCADE;")
                connection.connection.commit()
        except Exception as e:
            connection.connection.rollback()
