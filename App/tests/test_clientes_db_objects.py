import pytest
from django.db import connections

@pytest.mark.django_db
class TestClientesDBObjects:
    
    def test_sp_inserir_cliente(self, test_db_cursor):
        """
        Testa: CREATE - sp_inserir_cliente
        Valida: Inserção correta de cliente
        """
        cur = test_db_cursor
        
        # CALL ao primeiro procedure
        cur.execute(
            "CALL test_schema.sp_inserir_cliente(%s, %s, %s, %s);",
            ['Maria Silva', 'maria@email.com', '912345678', '123456789']
        )
        
        # SELECT para validar inserção
        cur.execute("""
            SELECT COUNT(*) FROM test_schema.clientes
            WHERE c_email = 'maria@email.com' AND c_nome = 'Maria Silva'
        """)
        
        contador = cur.fetchone()[0]
        assert contador == 1, "Erro: Cliente não foi inserido"
        
        # Validar dados específicos
        cur.execute("""
            SELECT c_telefone, nif FROM test_schema.clientes
            WHERE c_email = 'maria@email.com'
        """)
        
        resultado = cur.fetchone()
        assert resultado[0] == '912345678', "Erro: Telefone incorreto"
        assert resultado[1] == '123456789', "Erro: NIF incorreto"
        
        connections['default'].connection.commit()
        print("✓ Test sp_inserir_cliente: PASSOU")
    
    def test_sp_atualizar_cliente(self, test_db_cursor):
        """
        Testa: UPDATE - sp_atualizar_cliente
        Valida: Atualização correta de dados do cliente
        """
        cur = test_db_cursor
        
        # Setup: inserir cliente primeiro
        cur.execute(
            "CALL test_schema.sp_inserir_cliente(%s, %s, %s, %s);",
            ['João Santos', 'joao@email.com', '911111111', '111111111']
        )
        
        # CALL ao segundo procedure (atualização)
        cur.execute(
            "CALL test_schema.sp_atualizar_cliente(%s, %s, %s);",
            ['joao@email.com', '922222222', 'joao.novo@email.com']
        )
        
        # Validar atualização
        cur.execute("""
            SELECT c_telefone FROM test_schema.clientes
            WHERE c_email = 'joao.novo@email.com'
        """)
        
        resultado = cur.fetchone()
        assert resultado[0] == '922222222', "Erro: Telefone não foi atualizado"
        
        connections['default'].connection.commit()
        print("✓ Test sp_atualizar_cliente: PASSOU")
