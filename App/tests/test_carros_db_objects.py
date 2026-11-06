import pytest
from django.db import connections

@pytest.mark.django_db
class TestCarrosDBObjects:
    
    def test_sp_inserir_carro(self, test_db_cursor):
        """
        Testa: CREATE - sp_inserir_carro
        Valida: Inserção correta de carro
        """
        cur = test_db_cursor
        
        # Setup: criar marca e stand
        cur.execute("""
            INSERT INTO test_schema.marcas (país_origem, m_nome)
            VALUES ('Alemanha', 'BMW')
            RETURNING marca_id;
        """)
        marca_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.stands (nome, localizacao, contacto, email)
            VALUES ('Stand Test', 'Lisboa', '211234567', 'test@stand.com')
            RETURNING stand_id;
        """)
        stand_id = cur.fetchone()[0]
        
        # CALL ao primeiro procedure
        cur.execute(
            "CALL test_schema.sp_inserir_carro(%s, %s, %s, %s, %s, %s, %s);",
            [stand_id, marca_id, 'X5', 2023, 45000.00, 'novo', 0]
        )
        
        # Validar inserção
        cur.execute("""
            SELECT COUNT(*) FROM test_schema.carros
            WHERE modelo = 'X5' AND ano = 2023 AND estado = 'novo'
        """)
        
        contador = cur.fetchone()[0]
        assert contador == 1, "Erro: Carro não foi inserido"
        
        connections['default'].connection.commit()
        print("✓ Test sp_inserir_carro: PASSOU")
    
    def test_sp_marcar_carro_vendido(self, test_db_cursor):
        """
        Testa: UPDATE - sp_marcar_carro_vendido
        Valida: Carro marcado como vendido
        """
        cur = test_db_cursor
        
        # Setup: inserir carro primeiro
        cur.execute("""
            INSERT INTO test_schema.marcas (país_origem, m_nome)
            VALUES ('Itália', 'Fiat')
            RETURNING marca_id;
        """)
        marca_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO test_schema.stands (nome, localizacao, contacto, email)
            VALUES ('Stand Porto', 'Porto', '225234567', 'porto@test.com')
            RETURNING stand_id;
        """)
        stand_id = cur.fetchone()[0]
        
        cur.execute(
            "CALL test_schema.sp_inserir_carro(%s, %s, %s, %s, %s, %s, %s);",
            [stand_id, marca_id, '500', 2022, 25000.00, 'usado', 50000]
        )
        
        cur.execute("""
            SELECT carro_id FROM test_schema.carros
            WHERE modelo = '500' LIMIT 1
        """)
        carro_id = cur.fetchone()[0]
        
        # CALL ao segundo procedure
        cur.execute(
            "CALL test_schema.sp_marcar_carro_vendido(%s);",
            [carro_id]
        )
        
        # Validar que carro foi marcado como vendido
        cur.execute("""
            SELECT status_disponibilidade FROM test_schema.carros
            WHERE carro_id = %s
        """, [carro_id])
        
        status = cur.fetchone()[0]
        assert status == 'vendido', "Erro: Carro não foi marcado como vendido"
        
        connections['default'].connection.commit()
        print("✓ Test sp_marcar_carro_vendido: PASSOU")
