-- ============================================
-- TRIGGERS
-- ============================================

-- ============================================
-- CLIENTES
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_validar_email_cliente()
RETURNS TRIGGER AS $$
BEGIN
    --Valida formato de email
    IF NEW.c_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$' THEN
        RAISE EXCEPTION 'Email inválido: %', NEW.c_email;
    END IF;

    --Normaliza email (lowercase)
    NEW.c_email := LOWER(NEW.c_email);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_clientes_validar_email ON clientes;
CREATE TRIGGER tg_clientes_validar_email
BEFORE INSERT OR UPDATE ON clientes
FOR EACH ROW
EXECUTE FUNCTION fn_validar_email_cliente();

-- ============================================
-- CARROS
-- ============================================

--Lucas
CREATE OR REPLACE FUNCTION fn_carros_before_delete()
RETURNS TRIGGER AS $$
DECLARE
    v_vendas INT;
BEGIN
    SELECT COUNT(*) INTO v_vendas FROM vendas WHERE carro_id = OLD.carro_id;

    IF v_vendas > 0 THEN
        RAISE EXCEPTION 'Não é possível apagar carro com vendas associadas';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_carros_before_delete ON carros;
CREATE TRIGGER tg_carros_before_delete
BEFORE DELETE ON carros
FOR EACH ROW
EXECUTE FUNCTION fn_carros_before_delete();

-- ============================================
-- IMAGENS_CARROS
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_limitar_imagens_carro()
RETURNS TRIGGER AS $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count FROM imagens_carros WHERE carro_id = NEW.carro_id;
    IF v_count >= 20 THEN
        RAISE EXCEPTION 'Limite máximo de 20 imagens por carro atingido';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_limitar_imagens_carro ON imagens_carros;
CREATE TRIGGER tg_limitar_imagens_carro
BEFORE INSERT ON imagens_carros
FOR EACH ROW
EXECUTE FUNCTION fn_limitar_imagens_carro();

--Tiago
CREATE OR REPLACE FUNCTION fn_imagens_carro_atualizar_capa()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_capa = TRUE THEN
        UPDATE imagens_carros SET is_capa = FALSE WHERE carro_id = NEW.carro_id AND imagem_id != NEW.imagem_id;
        UPDATE carros SET ref_imagem_capa = NEW.blob_name WHERE carro_id = NEW.carro_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_imagens_carro_atualizar_capa ON imagens_carros;
CREATE TRIGGER tg_imagens_carro_atualizar_capa
AFTER INSERT OR UPDATE ON imagens_carros
FOR EACH ROW
EXECUTE FUNCTION fn_imagens_carro_atualizar_capa();

-- ============================================
-- VENDAS
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_vendas_before_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT fn_carro_disponivel(NEW.carro_id) THEN
        RAISE EXCEPTION 'Carro não disponível para venda (vendido ou reservado)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_vendas_before_insert ON vendas;
CREATE TRIGGER tg_vendas_before_insert
BEFORE INSERT ON vendas
FOR EACH ROW
EXECUTE FUNCTION fn_vendas_before_insert();

--Tiago
CREATE OR REPLACE FUNCTION fn_vendas_after_delete()
RETURNS TRIGGER AS $$
BEGIN
        UPDATE carros
        SET status_disponibilidade = 'disponivel'
        WHERE carro_id = OLD.carro_id
            AND status_disponibilidade = 'vendido';
        RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_vendas_after_delete ON vendas;
CREATE TRIGGER tg_vendas_after_delete
AFTER DELETE ON vendas
FOR EACH ROW
EXECUTE FUNCTION fn_vendas_after_delete();

-- ============================================
-- ORDENS_SERVICO
-- ============================================

--Guilherme
CREATE OR REPLACE FUNCTION fn_atualizar_status_os()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data_saida IS NOT NULL AND (OLD.data_saida IS NULL) THEN
        NEW.status := 'concluida';
    END IF;

    IF NEW.data_prevista_saida IS NOT NULL AND NEW.data_prevista_saida < CURRENT_DATE AND NEW.status NOT IN ('concluida', 'cancelada') THEN
        NEW.prioridade := 'urgente';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_ordens_servico_status ON ordens_servico;
CREATE TRIGGER tg_ordens_servico_status
BEFORE UPDATE ON ordens_servico
FOR EACH ROW
EXECUTE FUNCTION fn_atualizar_status_os();


-- ============================================
-- RESERVAS
-- ============================================

--Lucas
CREATE OR REPLACE FUNCTION fn_reservas_before_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT fn_carro_disponivel(NEW.carro_id) THEN
        RAISE EXCEPTION 'Carro não disponível para reserva';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_reservas_before_insert ON reservas;
CREATE TRIGGER tg_reservas_before_insert
BEFORE INSERT ON reservas
FOR EACH ROW
EXECUTE FUNCTION fn_reservas_before_insert();

--Lucas
CREATE OR REPLACE FUNCTION fn_reservas_after_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE carros
    SET status_disponibilidade = 'disponivel'
    WHERE carro_id = OLD.carro_id
      AND status_disponibilidade = 'reservado';
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_reservas_after_delete ON reservas;
CREATE TRIGGER tg_reservas_after_delete
AFTER DELETE ON reservas
FOR EACH ROW
EXECUTE FUNCTION fn_reservas_after_delete();

-- ============================================
-- PECAS_ACESSORIOS
-- ============================================

--Lucas
CREATE OR REPLACE FUNCTION fn_pecas_stock_alert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.stock_atual < NEW.stock_minimo AND OLD.stock_atual >= OLD.stock_minimo THEN
        RAISE NOTICE 'ALERTA: Stock baixo para peça % (ID: %). Stock atual: %, Mínimo: %', NEW.nome, NEW.peca_id, NEW.stock_atual, NEW.stock_minimo;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_pecas_stock_alert ON pecas_acessorios;
CREATE TRIGGER tg_pecas_stock_alert
AFTER UPDATE ON pecas_acessorios
FOR EACH ROW
EXECUTE FUNCTION fn_pecas_stock_alert();
