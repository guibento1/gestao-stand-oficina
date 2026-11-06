-- ============================================
-- PROCEDURES
-- ============================================

-- ============================================
-- CLIENTES
-- ============================================

--Guilherme
CREATE OR REPLACE PROCEDURE sp_inserir_cliente(
    p_nome VARCHAR,
    p_email VARCHAR,
    p_telefone VARCHAR,
    p_nif VARCHAR,
    p_data_nascimento DATE DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT fn_validar_nif(p_nif) THEN
        RAISE EXCEPTION 'NIF inválido: %', p_nif;
    END IF;

    INSERT INTO clientes (c_nome, c_email, c_telefone, nif, data_nascimento)
    VALUES (p_nome, p_email, p_telefone, p_nif, p_data_nascimento);
EXCEPTION
    WHEN unique_violation THEN
        IF SQLERRM LIKE '%c_email%' THEN
            RAISE EXCEPTION 'Já existe um cliente com este email: %', p_email;
        ELSIF SQLERRM LIKE '%nif%' THEN
            RAISE EXCEPTION 'Já existe um cliente com este NIF: %', p_nif;
        ELSE
            RAISE EXCEPTION 'Dados duplicados: %', SQLERRM;
        END IF;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_eliminar_cliente(p_cliente_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM vendas v WHERE v.cliente_id = p_cliente_id) THEN
        RAISE EXCEPTION 'Cliente tem vendas registadas';
    END IF;
    IF EXISTS (SELECT 1 FROM reservas r WHERE r.cliente_id = p_cliente_id) THEN
        RAISE EXCEPTION 'Cliente tem reservas activas';
    END IF;

    DELETE FROM clientes WHERE cliente_id = p_cliente_id;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_atualizar_cliente(
    p_cliente_id INT,
    p_nome VARCHAR,
    p_email VARCHAR,
    p_telefone VARCHAR,
    p_nif VARCHAR,
    p_data_nascimento DATE DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_nif IS NOT NULL AND NOT fn_validar_nif(p_nif) THEN
        RAISE EXCEPTION 'NIF inválido: %', p_nif;
    END IF;

    UPDATE clientes
    SET c_nome = p_nome,
        c_email = p_email,
        c_telefone = p_telefoSne,
        nif = p_nif,
        data_nascimento = p_data_nascimento
    WHERE cliente_id = p_cliente_id;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Email ou NIF duplicado: %', SQLERRM;
END;
$$;

-- ============================================
-- CARROS
-- ============================================

--Lucas
CREATE OR REPLACE PROCEDURE sp_inserir_carro(
    p_stand_id INT,
    p_marca_id INT,
    p_modelo VARCHAR,
    p_ano INT,
    p_preco DECIMAL,
    p_estado VARCHAR,
    p_quilometragem INT DEFAULT 0,
    p_cor VARCHAR DEFAULT NULL,
    p_chassi VARCHAR DEFAULT NULL,
    p_placa VARCHAR DEFAULT NULL,
    p_combustivel VARCHAR DEFAULT NULL,
    p_potencia INT DEFAULT NULL,
    p_ref_imagem_capa VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Validações
    IF p_estado NOT IN ('novo', 'seminovo', 'usado') THEN
        RAISE EXCEPTION 'Estado inválido: %. Use: novo, seminovo ou usado', p_estado;
    END IF;

    -- Normalizar strings vazias para NULL para evitar colisões na constraint UNIQUE
    IF p_chassi IS NOT NULL AND TRIM(p_chassi) = '' THEN
        p_chassi := NULL;
    END IF;
    IF p_placa IS NOT NULL AND TRIM(p_placa) = '' THEN
        p_placa := NULL;
    END IF;
    IF p_combustivel IS NOT NULL AND TRIM(p_combustivel) = '' THEN
        p_combustivel := NULL;
    END IF;

    INSERT INTO carros (stand_id, marca_id, modelo, ano, preco, estado, quilometragem, cor, chassi, placa, combustivel, potencia, ref_imagem_capa, data_aquisicao)
    VALUES (p_stand_id, p_marca_id, p_modelo, p_ano, p_preco, p_estado, p_quilometragem, p_cor, p_chassi, p_placa, p_combustivel, p_potencia, p_ref_imagem_capa, CURRENT_DATE);
EXCEPTION
    WHEN foreign_key_violation THEN
        IF SQLERRM LIKE '%stand_id%' THEN
            RAISE EXCEPTION 'Stand não existe: %', p_stand_id;
        ELSIF SQLERRM LIKE '%marca_id%' THEN
            RAISE EXCEPTION 'Marca não existe: %', p_marca_id;
        ELSE
            RAISE EXCEPTION 'Erro de referência: %', SQLERRM;
        END IF;
    WHEN unique_violation THEN
        IF SQLERRM LIKE '%chassi%' THEN
            RAISE EXCEPTION 'Violação de unicidade: já existe um carro com este chassi (%).', p_chassi;
        ELSIF SQLERRM LIKE '%placa%' THEN
            RAISE EXCEPTION 'Violação de unicidade: já existe um carro com esta placa (%).', p_placa;
        ELSE
            RAISE EXCEPTION 'Violação de unicidade: %', SQLERRM;
        END IF;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_eliminar_carro(p_carro_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Remover imagens associadas
    DELETE FROM imagens_carros WHERE carro_id = p_carro_id;

    -- Remover reservas e vendas associadas deve ser tratado por constraints ou por checks externos
    DELETE FROM reservas WHERE carro_id = p_carro_id;
    DELETE FROM vendas WHERE carro_id = p_carro_id;

    DELETE FROM carros WHERE carro_id = p_carro_id;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_atualizar_carro(
    p_carro_id INT,
    p_stand_id INT,
    p_marca_id INT,
    p_modelo VARCHAR,
    p_ano INT,
    p_preço DECIMAL,
    p_estado VARCHAR,
    p_quilometragem INT,
    p_cor VARCHAR,
    p_chassi VARCHAR,
    p_placa VARCHAR,
    p_status_disponibilidade VARCHAR,
    p_data_aquisicao DATE DEFAULT NULL,
    p_combustivel VARCHAR DEFAULT NULL,
    p_potencia INT DEFAULT NULL,
    p_cilindrada INT DEFAULT NULL,
    p_portas INT DEFAULT NULL,
    p_lugares INT DEFAULT NULL,
    p_ref_imagem_capa TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_estado IS NOT NULL AND p_estado NOT IN ('novo','seminovo','usado') THEN
        RAISE EXCEPTION 'Estado inválido: %', p_estado;
    END IF;

    IF p_combustivel IS NOT NULL AND TRIM(p_combustivel) = '' THEN
        p_combustivel := NULL;
    END IF;

    -- Normalizar strings vazias para NULL para evitar colisões na constraint UNIQUE
    IF p_chassi IS NOT NULL AND TRIM(p_chassi) = '' THEN
        p_chassi := NULL;
    END IF;
    IF p_placa IS NOT NULL AND TRIM(p_placa) = '' THEN
        p_placa := NULL;
    END IF;

    UPDATE carros SET
        stand_id = p_stand_id,
        marca_id = p_marca_id,
        modelo = p_modelo,
        ano = p_ano,
        preço = p_preço,
        estado = p_estado,
        quilometragem = p_quilometragem,
        cor = p_cor,
        chassi = p_chassi,
        placa = p_placa,
        status_disponibilidade = p_status_disponibilidade,
        data_aquisicao = p_data_aquisicao,
        combustivel = p_combustivel,
        potencia = p_potencia,
        cilindrada = p_cilindrada,
        portas = p_portas,
        lugares = p_lugares,
        ref_imagem_capa = p_ref_imagem_capa
    WHERE carro_id = p_carro_id;
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE EXCEPTION 'Referência inválida ao atualizar carro: %', SQLERRM;
    WHEN unique_violation THEN
        IF SQLERRM LIKE '%chassi%' THEN
            RAISE EXCEPTION 'Violação de unicidade: já existe um carro com este chassi (%).', p_chassi;
        ELSIF SQLERRM LIKE '%placa%' THEN
            RAISE EXCEPTION 'Violação de unicidade: já existe um carro com esta placa (%).', p_placa;
        ELSE
            RAISE EXCEPTION 'Violação de unicidade: %', SQLERRM;
        END IF;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_atualizar_ref_imagem_capa(p_carro_id integer, p_blob_name text)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE carros SET ref_imagem_capa = p_blob_name WHERE carro_id = p_carro_id;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_limpar_ref_imagem_capa(p_carro_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE carros SET ref_imagem_capa = NULL WHERE carro_id = p_carro_id;
END;
$$;

-- ============================================
-- VENDAS
-- ============================================

--Guilherme
CREATE OR REPLACE PROCEDURE sp_registar_venda(
    p_cliente_id INT,
    p_carro_id INT,
    p_preco_final DECIMAL,
    p_funcionario_id INT DEFAULT NULL,
    p_forma_pagamento VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_venda_id INT;
BEGIN
    IF NOT fn_carro_disponivel(p_carro_id) THEN
        RAISE EXCEPTION 'Carro não disponível para venda';
    END IF;

    INSERT INTO vendas (cliente_id, carro_id, preco_final, funcionario_id, forma_pagamento)
    VALUES (p_cliente_id, p_carro_id, p_preco_final, p_funcionario_id, p_forma_pagamento)
    RETURNING venda_id INTO v_venda_id;

    UPDATE carros SET status_disponibilidade = 'vendido' WHERE carro_id = p_carro_id;

    UPDATE reservas SET estado = 'cancelada' WHERE carro_id = p_carro_id AND estado IN ('pendente', 'confirmada');
EXCEPTION
    WHEN foreign_key_violation THEN
        IF SQLERRM LIKE '%cliente_id%' THEN
            RAISE EXCEPTION 'Cliente não existe: %', p_cliente_id;
        ELSIF SQLERRM LIKE '%carro_id%' THEN
            RAISE EXCEPTION 'Carro não existe: %', p_carro_id;
        ELSE
            RAISE EXCEPTION 'Erro de referência: %', SQLERRM;
        END IF;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_eliminar_venda(p_venda_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM vendas WHERE venda_id = p_venda_id;
END;
$$;
$$;

-- ============================================
-- RESERVAS
-- ============================================

--Lucas
CREATE OR REPLACE PROCEDURE sp_reservar_carro(
    p_cliente_id INT,
    p_carro_id INT
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT fn_carro_disponivel(p_carro_id) THEN
        RAISE EXCEPTION 'Carro não disponível para reserva';
    END IF;

    INSERT INTO reservas (cliente_id, carro_id, estado)
    VALUES (p_cliente_id, p_carro_id, 'confirmada');

    UPDATE carros SET status_disponibilidade = 'reservado' WHERE carro_id = p_carro_id;
EXCEPTION
    WHEN foreign_key_violation THEN
        IF SQLERRM LIKE '%cliente_id%' THEN
            RAISE EXCEPTION 'Cliente não existe: %', p_cliente_id;
        ELSIF SQLERRM LIKE '%carro_id%' THEN
            RAISE EXCEPTION 'Carro não existe: %', p_carro_id;
        ELSE
            RAISE EXCEPTION 'Erro de referência: %', SQLERRM;
        END IF;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_atualizar_reserva(p_reserva_id integer, p_estado text)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE reservas SET estado = p_estado WHERE reserva_id = p_reserva_id;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_eliminar_reserva(p_reserva_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM reservas WHERE reserva_id = p_reserva_id;
END;
$$;

-- ============================================
-- AVALIAÇÕES
-- ============================================

--Tiago
CREATE OR REPLACE PROCEDURE sp_inserir_avaliacao(
    p_cliente_id INT,
    p_tipo_avaliacao VARCHAR,
    p_classificacao INT,
    p_carro_id INT DEFAULT NULL,
    p_ordem_servico_id INT DEFAULT NULL,
    p_comentario TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_classificacao < 1 OR p_classificacao > 5 THEN
        RAISE EXCEPTION 'Classificação deve ser entre 1 e 5: %', p_classificacao;
    END IF;

    IF p_tipo_avaliacao NOT IN ('venda', 'servico') THEN
        RAISE EXCEPTION 'Tipo de avaliação inválido: %. Use: venda ou servico', p_tipo_avaliacao;
    END IF;

    IF p_tipo_avaliacao = 'venda' AND p_carro_id IS NULL THEN
        RAISE EXCEPTION 'Avaliação de venda requer carro_id';
    END IF;
    IF p_tipo_avaliacao = 'servico' AND p_ordem_servico_id IS NULL THEN
        RAISE EXCEPTION 'Avaliação de serviço requer ordem_servico_id';
    END IF;

    INSERT INTO avaliacoes (cliente_id, carro_id, ordem_servico_id, tipo_avaliacao, classificacao, comentario)
    VALUES (p_cliente_id, p_carro_id, p_ordem_servico_id, p_tipo_avaliacao, p_classificacao, p_comentario);
EXCEPTION
    WHEN foreign_key_violation THEN
        IF SQLERRM LIKE '%cliente_id%' THEN
            RAISE EXCEPTION 'Cliente não existe: %', p_cliente_id;
        ELSIF SQLERRM LIKE '%carro_id%' THEN
            RAISE EXCEPTION 'Carro não existe: %', p_carro_id;
        ELSIF SQLERRM LIKE '%ordem_servico_id%' THEN
            RAISE EXCEPTION 'Ordem de serviço não existe: %', p_ordem_servico_id;
        ELSE
            RAISE EXCEPTION 'Erro de referência: %', SQLERRM;
        END IF;
END;
$$;

--Tiago
CREATE OR REPLACE PROCEDURE sp_eliminar_avaliacao(p_avaliacao_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM avaliacoes WHERE avaliacao_id = p_avaliacao_id;
END;
$$;


--Tiago
CREATE OR REPLACE PROCEDURE sp_eliminar_avaliacao_por_utilizador(
    p_avaliacao_id integer,
    p_requester_email varchar
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_role text;
    v_cliente_id int;
    v_deleted int;
BEGIN
    SELECT role, cliente_id INTO v_role, v_cliente_id FROM utilizadores WHERE email = p_requester_email;
    IF v_role IS NULL THEN
        RAISE EXCEPTION 'Utilizador não encontrado';
    END IF;

    IF v_role IN ('admin','gerente','funcionario') THEN
        DELETE FROM avaliacoes WHERE avaliacao_id = p_avaliacao_id;
        RETURN;
    END IF;

    IF v_cliente_id IS NOT NULL THEN
        DELETE FROM avaliacoes WHERE avaliacao_id = p_avaliacao_id AND cliente_id = v_cliente_id;
        GET DIAGNOSTICS v_deleted = ROW_COUNT;
        IF v_deleted = 0 THEN
            RAISE EXCEPTION 'Não tem permissão para eliminar esta avaliação ou não existe';
        END IF;
        RETURN;
    END IF;

    RAISE EXCEPTION 'Não tem permissão para eliminar esta avaliação';
END;
$$;

-- ============================================
-- ORDENS DE SERVIÇO
-- ============================================

--Tiago
CREATE OR REPLACE PROCEDURE sp_criar_os(
    p_carro_id INT,
    p_cliente_id INT,
    p_tipo_servico_id INT,
    p_valor_mao_obra DECIMAL,
    p_mecanico_id INT DEFAULT NULL,
    p_baia_id INT DEFAULT NULL,
    p_data_prevista TIMESTAMP DEFAULT NULL,
    p_prioridade VARCHAR DEFAULT 'normal',
    p_diagnostico TEXT DEFAULT NULL,
    p_observacoes TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_nome_veiculo VARCHAR := NULL;
BEGIN
    IF p_carro_id IS NOT NULL THEN
        SELECT modelo INTO v_nome_veiculo FROM carros WHERE carro_id = p_carro_id;
    END IF;

    IF v_nome_veiculo IS NULL THEN
        v_nome_veiculo := '---';
    END IF;

    INSERT INTO ordens_servico (cliente_id, nome_veiculo, tipo_servico_id, mecanico_id, baia_id, data_prevista_saida, prioridade, descricao_problema, observacoes, valor_total, criado_por_id)
    VALUES (p_cliente_id, v_nome_veiculo, p_tipo_servico_id, p_mecanico_id, p_baia_id, p_data_prevista, p_prioridade, p_diagnostico, p_observacoes, COALESCE(p_valor_mao_obra,0), NULL);
EXCEPTION
    WHEN foreign_key_violation THEN
        IF SQLERRM LIKE '%cliente_id%' THEN
            RAISE EXCEPTION 'Cliente não existe: %', p_cliente_id;
        ELSIF SQLERRM LIKE '%tipo_servico_id%' THEN
            RAISE EXCEPTION 'Tipo de serviço não existe: %', p_tipo_servico_id;
        ELSIF SQLERRM LIKE '%mecanico_id%' THEN
            RAISE EXCEPTION 'Mecânico não existe: %', p_mecanico_id;
        ELSIF SQLERRM LIKE '%baia_id%' THEN
            RAISE EXCEPTION 'Baia não existe: %', p_baia_id;
        ELSE
            RAISE EXCEPTION 'Erro de referência: %', SQLERRM;
        END IF;
END;
$$;

--Lucas
CREATE OR REPLACE PROCEDURE sp_concluir_os(
    p_ordem_servico_id INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_valor_pecas DECIMAL := 0;
    v_valor_mao_obra DECIMAL := 0;
    v_status VARCHAR;
BEGIN
    SELECT status INTO v_status FROM ordens_servico WHERE ordem_servico_id = p_ordem_servico_id;

    IF v_status IS NULL THEN
        RAISE EXCEPTION 'Ordem de serviço não encontrada: %', p_ordem_servico_id;
    END IF;

    IF v_status = 'concluida' THEN
        RAISE EXCEPTION 'Ordem de serviço já está concluída';
    END IF;


    SELECT COALESCE(valor_mao_obra, 0) INTO v_valor_mao_obra FROM ordens_servico WHERE ordem_servico_id = p_ordem_servico_id;

    UPDATE ordens_servico
    SET status = 'concluida',
        data_saida = NOW(),
        valor_pecas = v_valor_pecas,
        valor_total = COALESCE(v_valor_mao_obra,0) + v_valor_pecas
    WHERE ordem_servico_id = p_ordem_servico_id;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_eliminar_os(
    p_ordem_servico_id INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_status VARCHAR;
BEGIN
    SELECT status INTO v_status FROM ordens_servico WHERE ordem_servico_id = p_ordem_servico_id;

    IF v_status IS NULL THEN
        RAISE EXCEPTION 'Ordem de serviço não encontrada: %', p_ordem_servico_id;
    END IF;

    IF v_status != 'concluida' THEN
        RAISE EXCEPTION 'Apenas ordens concluídas podem ser eliminadas';
    END IF;

    DELETE FROM ordens_servico WHERE ordem_servico_id = p_ordem_servico_id;
END;
$$;

-- ============================================
-- IMAGENS_CARROS
-- ============================================

--Guilherme
CREATE OR REPLACE PROCEDURE sp_eliminar_imagem_carro(p_imagem_id integer)
LANGUAGE plpgsql
AS $$
DECLARE
    v_blob_name text;
    v_carro_id integer;
BEGIN
    SELECT blob_name, carro_id INTO v_blob_name, v_carro_id
    FROM imagens_carros WHERE imagem_id = p_imagem_id;

    IF v_blob_name IS NULL THEN
        RAISE NOTICE 'Imagem % não encontrada', p_imagem_id;
        RETURN;
    END IF;

    DELETE FROM imagens_carros WHERE imagem_id = p_imagem_id;

    IF v_carro_id IS NOT NULL THEN
        -- limpar ref_imagem_capa se apontava para esta imagem
        UPDATE carros
        SET ref_imagem_capa = NULL
        WHERE carro_id = v_carro_id AND ref_imagem_capa = v_blob_name;
    END IF;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_inserir_imagem_carro(
    p_carro_id integer,
    p_blob_name text,
    p_descricao text,
    p_ordem integer,
    p_is_capa boolean,
    p_uploaded_by integer)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_is_capa THEN
        UPDATE imagens_carros SET is_capa = FALSE WHERE carro_id = p_carro_id;
    END IF;

    INSERT INTO imagens_carros (carro_id, blob_name, descricao, ordem, is_capa, uploaded_by, created_at, updated_at)
    VALUES (p_carro_id, p_blob_name, p_descricao, p_ordem, p_is_capa, p_uploaded_by, NOW(), NOW());

    -- Atualizar referência do carro para a imagem de capa se necessário
    IF p_is_capa THEN
        UPDATE carros SET ref_imagem_capa = p_blob_name WHERE carro_id = p_carro_id;
    END IF;
END;
$$;

--Guilherme
CREATE OR REPLACE PROCEDURE sp_atualizar_imagem_carro(
    p_imagem_id integer,
    p_descricao text,
    p_ordem integer,
    p_is_capa boolean)
LANGUAGE plpgsql
AS $$
DECLARE
    v_carro_id integer;
    v_blob text;
BEGIN
    SELECT carro_id, blob_name INTO v_carro_id, v_blob FROM imagens_carros WHERE imagem_id = p_imagem_id;
    IF v_carro_id IS NULL THEN
        RAISE EXCEPTION 'Imagem % não encontrada', p_imagem_id;
    END IF;

    IF p_is_capa THEN
        UPDATE imagens_carros SET is_capa = FALSE WHERE carro_id = v_carro_id;
    END IF;

    UPDATE imagens_carros
    SET descricao = p_descricao,
        ordem = p_ordem,
        is_capa = p_is_capa,
        updated_at = NOW()
    WHERE imagem_id = p_imagem_id;

    IF p_is_capa THEN
        UPDATE carros SET ref_imagem_capa = v_blob WHERE carro_id = v_carro_id;
    ELSE
        -- se foi removida a capa e era referência, limpar
        UPDATE carros SET ref_imagem_capa = NULL
        WHERE carro_id = v_carro_id AND ref_imagem_capa = v_blob;
    END IF;
END;
$$;

-- ============================================
-- UTILIZADORES
-- ===========================================

--Guilherme 
CREATE OR REPLACE PROCEDURE sp_atualizar_last_login(p_user_id integer)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE utilizadores SET last_login = NOW() WHERE user_id = p_user_id;
END;
$$;