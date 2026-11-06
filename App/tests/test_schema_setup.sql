CREATE SCHEMA IF NOT EXISTS test_schema;

CREATE TABLE IF NOT EXISTS test_schema.marcas (
    marca_id SERIAL PRIMARY KEY,
    país_origem VARCHAR(100),
    m_nome VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS test_schema.stands (
    stand_id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    localizacao VARCHAR(200),
    contacto VARCHAR(20),
    email VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS test_schema.clientes (
    cliente_id SERIAL PRIMARY KEY,
    c_nome VARCHAR(200) NOT NULL,
    c_email VARCHAR(100) UNIQUE NOT NULL,
    c_telefone VARCHAR(20),
    nif VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS test_schema.carros (
    carro_id SERIAL PRIMARY KEY,
    stand_id INTEGER REFERENCES test_schema.stands(stand_id),
    marca_id INTEGER REFERENCES test_schema.marcas(marca_id),
    modelo VARCHAR(100),
    ano INTEGER,
    preco DECIMAL(10,2),
    estado VARCHAR(20),
    quilometragem INTEGER,
    status_disponibilidade VARCHAR(20) DEFAULT 'disponível'
);

CREATE TABLE IF NOT EXISTS test_schema.vendas (
    venda_id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES test_schema.clientes(cliente_id),
    carro_id INTEGER REFERENCES test_schema.carros(carro_id),
    data_venda DATE,
    preco_final DECIMAL(10,2)
);

CREATE OR REPLACE PROCEDURE test_schema.sp_inserir_cliente(
    p_nome VARCHAR,
    p_email VARCHAR,
    p_telefone VARCHAR,
    p_nif VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO test_schema.clientes (c_nome, c_email, c_telefone, nif)
    VALUES (p_nome, p_email, p_telefone, p_nif);
END;
$$;

CREATE OR REPLACE PROCEDURE test_schema.sp_atualizar_cliente(
    p_email_antigo VARCHAR,
    p_telefone_novo VARCHAR,
    p_email_novo VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE test_schema.clientes
    SET c_telefone = p_telefone_novo,
        c_email = p_email_novo
    WHERE c_email = p_email_antigo;
END;
$$;

CREATE OR REPLACE PROCEDURE test_schema.sp_inserir_carro(
    p_stand_id INTEGER,
    p_marca_id INTEGER,
    p_modelo VARCHAR,
    p_ano INTEGER,
    p_preco DECIMAL,
    p_estado VARCHAR,
    p_quilometragem INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO test_schema.carros (stand_id, marca_id, modelo, ano, preco, estado, quilometragem, status_disponibilidade)
    VALUES (p_stand_id, p_marca_id, p_modelo, p_ano, p_preco, p_estado, p_quilometragem, 'disponível');
END;
$$;

CREATE OR REPLACE PROCEDURE test_schema.sp_marcar_carro_vendido(
    p_carro_id INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE test_schema.carros
    SET status_disponibilidade = 'vendido'
    WHERE carro_id = p_carro_id;
END;
$$;

CREATE OR REPLACE PROCEDURE test_schema.sp_registar_venda(
    p_cliente_id INTEGER,
    p_carro_id INTEGER,
    p_data_venda DATE,
    p_preco_final DECIMAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO test_schema.vendas (cliente_id, carro_id, data_venda, preco_final)
    VALUES (p_cliente_id, p_carro_id, p_data_venda, p_preco_final);
    
    CALL test_schema.sp_marcar_carro_vendido(p_carro_id);
END;
$$;

CREATE OR REPLACE PROCEDURE test_schema.sp_cancelar_venda(
    p_venda_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_carro_id INTEGER;
BEGIN
    SELECT carro_id INTO v_carro_id
    FROM test_schema.vendas
    WHERE venda_id = p_venda_id;
    
    DELETE FROM test_schema.vendas 
    WHERE venda_id = p_venda_id;
    
    UPDATE test_schema.carros
    SET status_disponibilidade = 'disponível'
    WHERE carro_id = v_carro_id;
END;
$$;
