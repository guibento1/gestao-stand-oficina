import pytest
from django.db import connections
from datetime import date

@pytest.mark.django_db
class TestVendasDBObjects:
    
    def test_sp_registar_venda(self, test_db_cursor):
        """
        Testa: CREATE - sp_registar_venda
        Valida: Venda criada e carro marcado como vendido
        """
        cur = test_db_cursor
        
        # Setup: criar cliente, marca, stand e carro
        cur.execute(
            "CALL test_schema.sp_inserir_cliente(%s, %s, %s, %s);",
            ['Carlos Pereira', 'carlos@email.com', '912345680', '987654321']
        )
        
        cur.execute("""
            SELECT cliente_id FROM test_schema.clientes 
            WHERE c_email = 'carlos@email.com'
        """)
        cliente_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.marcas (país_origem, m_nome)
            VALUES ('Itália', 'Fiat')
            RETURNING marca_id;
        """)
        marca_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.stands (nome, localizacao, contacto, email)
            VALUES ('Stand Test', 'Porto', '225234567', 'porto@test.com')
            RETURNING stand_id;
        """)
        stand_id = cur.fetchone()[0]
        
        cur.execute(
            "CALL test_schema.sp_inserir_carro(%s, %s, %s, %s, %s, %s, %s);",
            [stand_id, marca_id, 'Punto', 2020, 15000.00, 'usado', 80000]
        )
        
        cur.execute("""
            SELECT carro_id FROM test_schema.carros
            WHERE modelo = 'Punto' LIMIT 1
        """)
        carro_id = cur.fetchone()[0]
        
        # CALL ao primeiro procedure
        cur.execute(
            "CALL test_schema.sp_registar_venda(%s, %s, %s, %s);",
            [cliente_id, carro_id, date.today(), 14500.00]
        )
        
        # Validar venda
        cur.execute("""
            SELECT COUNT(*) FROM test_schema.vendas
            WHERE cliente_id = %s AND carro_id = %s
        """, [cliente_id, carro_id])
        
        contador = cur.fetchone()[0]
        assert contador == 1, "Erro: Venda não foi registada"
        
        connections['default'].connection.commit()
        print("✓ Test sp_registar_venda: PASSOU")
    
    def test_sp_cancelar_venda(self, test_db_cursor):
        """
        Testa: DELETE - sp_cancelar_venda
        Valida: Venda cancelada e carro volta a disponível
        """
        cur = test_db_cursor
        
        # Setup: criar venda primeiro (com todos os steps anteriores)
        cur.execute(
            "CALL test_schema.sp_inserir_cliente(%s, %s, %s, %s);",
            ['Ana Costa', 'ana@email.com', '913456789', '456789123']
        )
        
        cur.execute("""
            SELECT cliente_id FROM test_schema.clientes 
            WHERE c_email = 'ana@email.com'
        """)
        cliente_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.marcas (país_origem, m_nome)
            VALUES ('França', 'Peugeot')
            RETURNING marca_id;
        """)
        marca_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.stands (nome, localizacao, contacto, email)
            VALUES ('Stand Covilhã', 'Covilhã', '275345678', 'covilha@test.com')
            RETURNING stand_id;
        """)
        stand_id = cur.fetchone()[0]
        
        cur.execute(
            "CALL test_schema.sp_inserir_carro(%s, %s, %s, %s, %s, %s, %s);",
            [stand_id, marca_id, '308', 2019, 18000.00, 'novo', 0]
        )
        
        cur.execute("""
            SELECT carro_id FROM test_schema.carros
            WHERE modelo = '308' LIMIT 1
        """)
        carro_id = cur.fetchone()[0]
        
        cur.execute(
            "CALL test_schema.sp_registar_venda(%s, %s, %s, %s);",
            [cliente_id, carro_id, date.today(), 17500.00]
        )
        
        cur.execute("""
            SELECT venda_id FROM test_schema.vendas
            WHERE cliente_id = %s LIMIT 1
        """, [cliente_id])
        venda_id = cur.fetchone()[0]
        
        # CALL ao segundo procedure
        cur.execute(
            "CALL test_schema.sp_cancelar_venda(%s);",
            [venda_id]
        )
        
        # Validar que venda foi cancelada
        cur.execute("""
            SELECT COUNT(*) FROM test_schema.vendas
            WHERE venda_id = %s
        """, [venda_id])
        
        contador = cur.fetchone()[0]
        assert contador == 0, "Erro: Venda não foi cancelada"
        
        connections['default'].connection.commit()
        print("✓ Test sp_cancelar_venda: PASSOU")
