-- ============================================
-- UDFS
-- ============================================

-- ============================================
-- Utilizadores
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_autenticar_utilizador(p_email VARCHAR, p_password VARCHAR)
RETURNS TABLE(
    user_id INT,
    email VARCHAR,
    role VARCHAR,
    ativo BOOLEAN,
    nome TEXT,
    admin_id INT,
    gerente_id INT,
    funcionario_id INT,
    mecanico_id INT,
    cliente_id INT
)
LANGUAGE sql AS $$
SELECT u.user_id, u.email, u.role, u.ativo,
       COALESCE(a.nome, g.nome, f.f_nome, m.nome, c.c_nome) AS nome,
       u.admin_id, u.gerente_id, u.funcionario_id, u.mecanico_id, u.cliente_id
FROM utilizadores u
LEFT JOIN admins a ON u.admin_id = a.admin_id
LEFT JOIN gerentes g ON u.gerente_id = g.gerente_id
LEFT JOIN funcionarios f ON u.funcionario_id = f.funcionario_id
LEFT JOIN mecanicos m ON u.mecanico_id = m.mecanico_id
LEFT JOIN clientes c ON u.cliente_id = c.cliente_id
WHERE u.email = p_email
  AND u.ativo = true
  AND u.password_hash = crypt(p_password, u.password_hash);
$$;

-- ============================================
-- ORDENS_SERVICO
-- ============================================

--Tiago
CREATE OR REPLACE FUNCTION fn_exportar_ordens_servico(
    p_data_inicio DATE,
    p_data_fim DATE,
    p_status VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    ordem_servico_id INT,
    cliente_nome VARCHAR,
    cliente_nif VARCHAR,
    carro_modelo VARCHAR,
    carro_placa VARCHAR,
    mecanico_nome VARCHAR,
    tipo_servico VARCHAR,
    status VARCHAR,
    prioridade VARCHAR,
    data_entrada TIMESTAMP,
    data_prevista TIMESTAMP,
    data_conclusao TIMESTAMP,
    valor_mao_obra NUMERIC,
    valor_pecas NUMERIC,
    valor_total NUMERIC,
    stand_nome VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        os.ordem_servico_id,
        c.c_nome,
        c.nif,
        os.nome_veiculo AS carro_modelo,
        NULL::VARCHAR AS carro_placa,
        me.nome,
        ts.nome,
        os.status,
        os.prioridade,
        os.data_entrada,
        os.data_prevista_saida,
        os.data_saida,
        0::NUMERIC AS valor_mao_obra,
        0::NUMERIC AS valor_pecas,
        COALESCE(os.valor_total, 0)::NUMERIC AS valor_total,
        s.nome
    FROM ordens_servico os
    INNER JOIN clientes c ON os.cliente_id = c.cliente_id
    LEFT JOIN mecanicos me ON os.mecanico_id = me.mecanico_id
    LEFT JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
    CROSS JOIN (SELECT NULL::VARCHAR AS nome) s
    WHERE os.data_entrada::DATE BETWEEN p_data_inicio AND p_data_fim
      AND (p_status IS NULL OR os.status = p_status)
    ORDER BY os.data_entrada DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STANDS
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_exportar_relatorio_financeiro(
    p_mes INT,
    p_ano INT
)
RETURNS TABLE (
    stand_nome VARCHAR,
    total_vendas_carros BIGINT,
    receita_vendas_carros NUMERIC,
    total_servicos_oficina BIGINT,
    receita_servicos_oficina NUMERIC,
    receita_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH vendas_mes AS (
        SELECT
            ca.stand_id,
            COUNT(v.venda_id) AS total_vendas,
            COALESCE(SUM(v.preco_final), 0) AS receita_vendas
        FROM vendas v
        INNER JOIN carros ca ON v.carro_id = ca.carro_id
        WHERE EXTRACT(MONTH FROM v.data) = p_mes
          AND EXTRACT(YEAR FROM v.data) = p_ano
        GROUP BY ca.stand_id
    ),
    servicos_mes AS (
        SELECT
            s.stand_id,
            0::BIGINT AS total_servicos,
            0::NUMERIC AS receita_servicos
        FROM stands s
    )
    SELECT
        s.nome,
        COALESCE(vm.total_vendas, 0),
        COALESCE(vm.receita_vendas, 0)::NUMERIC,
        COALESCE(sm.total_servicos, 0),
        COALESCE(sm.receita_servicos, 0)::NUMERIC,
        (COALESCE(vm.receita_vendas, 0) + COALESCE(sm.receita_servicos, 0))::NUMERIC AS receita_total
    FROM stands s
    LEFT JOIN vendas_mes vm ON s.stand_id = vm.stand_id
    LEFT JOIN servicos_mes sm ON s.stand_id = sm.stand_id
    ORDER BY receita_total DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- CARROS
-- ============================================

--Lucas
CREATE OR REPLACE FUNCTION fn_exportar_inventario_carros()
RETURNS TABLE (
    carro_id INT,
    stand_nome VARCHAR,
    marca VARCHAR,
    modelo VARCHAR,
    ano INT,
    estado VARCHAR,
    quilometragem INT,
    cor VARCHAR,
    chassi VARCHAR,
    placa VARCHAR,
    preço NUMERIC,
    status_disponibilidade VARCHAR,
    combustivel VARCHAR,
    potencia INT,
    data_aquisicao DATE,
    imagem_capa VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.carro_id,
        s.nome,
        m.m_nome,
        c.modelo,
        c.ano,
        c.estado,
        c.quilometragem,
        c.cor,
        c.chassi,
        c.placa,
        c.preço,
        c.status_disponibilidade,
        c.combustivel,
        c.potencia,
        c.data_aquisicao,
        c.ref_imagem_capa
    FROM carros c
    INNER JOIN stands s ON c.stand_id = s.stand_id
    INNER JOIN marcas m ON c.marca_id = m.marca_id
    ORDER BY s.nome, m.m_nome, c.modelo;
END;
$$ LANGUAGE plpgsql;

--Lucas
CREATE OR REPLACE FUNCTION fn_carro_disponivel(p_carro_id INT)
RETURNS BOOLEAN AS $$
DECLARE
    v_status VARCHAR;
BEGIN
    SELECT status_disponibilidade INTO v_status
    FROM carros
    WHERE carro_id = p_carro_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    RETURN v_status = 'disponivel';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- CLIENTES
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_validar_nif(p_nif TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_nif TEXT;
    v_soma INT := 0;
    v_digito_controlo INT;
    i INT;
BEGIN
    v_nif := TRIM(p_nif);

    IF LENGTH(v_nif) < 9 OR LENGTH(v_nif) > 13 THEN
        RETURN FALSE;
    END IF;

    IF v_nif !~ '^[0-9]+$' THEN
        RETURN FALSE;
    END IF;

    IF LENGTH(v_nif) = 9 THEN
        IF SUBSTRING(v_nif, 1, 1) NOT IN ('1', '2', '3', '5', '6', '7', '8', '9') THEN
            RETURN FALSE;
        END IF;

        FOR i IN 1..8 LOOP
            v_soma := v_soma + (CAST(SUBSTRING(v_nif, i, 1) AS INT) * (10 - i));
        END LOOP;

        v_digito_controlo := 11 - (v_soma % 11);

        IF v_digito_controlo >= 10 THEN
            v_digito_controlo := 0;
        END IF;

        RETURN v_digito_controlo = CAST(SUBSTRING(v_nif, 9, 1) AS INT);
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- RESERVAS
-- ============================================

--Lucas
CREATE OR REPLACE FUNCTION fn_reserva_disponivel(
    p_carro_id INT,
    p_inicio DATE,
    p_fim DATE
)
RETURNS BOOLEAN AS $$
DECLARE
    v_conflito INT;
BEGIN
    SELECT COUNT(*) INTO v_conflito
    FROM reservas r
    WHERE r.carro_id = p_carro_id
      AND r.estado IN ('pendente', 'confirmada')
      AND r.data_reserva BETWEEN p_inicio AND p_fim;

    RETURN v_conflito = 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- BAIAS_OFICINA
-- ============================================

--Tiago
CREATE OR REPLACE FUNCTION fn_baia_disponivel(
    p_baia_id INT,
    p_data_hora TIMESTAMP
)
RETURNS BOOLEAN AS $$
DECLARE
    v_status VARCHAR;
    v_conflito INT;
BEGIN
    SELECT status INTO v_status
    FROM baias_oficina
    WHERE baia_id = p_baia_id;

    IF NOT FOUND OR v_status != 'disponivel' THEN
        RETURN FALSE;
    END IF;

    SELECT COUNT(*) INTO v_conflito
    FROM ordens_servico os
    WHERE os.baia_id = p_baia_id
      AND os.status IN ('aguardando', 'em_andamento', 'pausado')
      AND os.data_entrada::DATE = p_data_hora::DATE;

    RETURN v_conflito = 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- IMAGENS_CARROS
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_gerar_url_imagem(p_blob_name VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_base_url VARCHAR := 'https://standoficinabd2.blob.core.windows.net/imagens/';
BEGIN
    IF p_blob_name IS NULL OR p_blob_name = '' THEN
        RETURN NULL;
    END IF;

    RETURN v_base_url || p_blob_name;
END;
$$ LANGUAGE plpgsql;

