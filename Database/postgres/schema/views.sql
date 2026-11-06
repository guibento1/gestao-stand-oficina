-- ============================================
-- VIEWS SIMPLES
-- ============================================

-- ============================================
-- UTILIZADORES
-- ============================================

--Guilherme
CREATE OR REPLACE VIEW vw_clientes_utilizadores AS
SELECT u.email, c.cliente_id, c.c_nome
FROM utilizadores u
JOIN clientes c ON u.cliente_id = c.cliente_id;

-- ============================================
-- AVALIACOES (detalhadas)
-- ============================================

--Guilherme
CREATE OR REPLACE VIEW vw_avaliacoes_detalhes AS
SELECT
    a.avaliacao_id,
    a.cliente_id,
    c.c_nome AS cliente_nome,
    a.carro_id,
    CASE WHEN a.carro_id IS NOT NULL
         THEN m.m_nome || ' ' || ca.modelo || ' (' || ca.ano || ')'
    END AS carro_info,
    a.ordem_servico_id,
    CASE WHEN a.ordem_servico_id IS NOT NULL
         THEN ts.nome || ' - ' || os.nome_veiculo
    END AS servico_info,
    a.tipo_avaliacao,
    a.classificacao,
    a.comentario,
    a.data_avaliacao
FROM avaliacoes a
JOIN clientes c ON a.cliente_id = c.cliente_id
LEFT JOIN carros ca ON a.carro_id = ca.carro_id
LEFT JOIN marcas m ON ca.marca_id = m.marca_id
LEFT JOIN ordens_servico os ON a.ordem_servico_id = os.ordem_servico_id
LEFT JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
ORDER BY a.data_avaliacao DESC;

-- ============================================
-- VENDAS
-- ============================================

--Tiago
CREATE OR REPLACE VIEW vw_vendas_completas AS
SELECT
    v.venda_id,
    v.data,
    c.c_nome AS cliente,
    ca.modelo AS carro,
    m.m_nome AS marca,
    v.preco_final,
    f.f_nome AS funcionario
FROM vendas v
INNER JOIN clientes c ON v.cliente_id = c.cliente_id
INNER JOIN carros ca ON v.carro_id = ca.carro_id
INNER JOIN marcas m ON ca.marca_id = m.marca_id
LEFT JOIN funcionarios f ON v.funcionario_id = f.funcionario_id;

-- ============================================
-- CARROS
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_carros_disponiveis AS
SELECT
    c.carro_id,
    c.marca_id,
    c.stand_id,
    c.modelo,
    c.ano,
    c.preço AS preco,
    c.preço AS "preço",
    c.estado,
    c.quilometragem,
    c.cor,
    c.status_disponibilidade,
    c.data_aquisicao,
    c.cilindrada,
    c.portas,
    c.lugares,
    c.ref_imagem_capa
FROM carros c
WHERE c.status_disponibilidade = 'disponivel';

--Lucas 
CREATE OR REPLACE VIEW vw_carros_completos AS
SELECT
    c.carro_id,
    c.marca_id,
    c.stand_id,
    m.m_nome AS marca,
    c.modelo,
    c.ano,
    c.preço AS preco,
    c.preço AS "preço",
    c.estado,
    c.status_disponibilidade,
    s.localizacao AS stand,
    c.quilometragem,
    c.cor,
    c.chassi,
    c.placa,
    c.combustivel,
    c.potencia,
    c.cilindrada,
    c.portas,
    c.lugares,
    c.data_aquisicao,
    c.ref_imagem_capa
FROM carros c
JOIN marcas m ON c.marca_id = m.marca_id
JOIN stands s ON c.stand_id = s.stand_id
ORDER BY m.m_nome, c.modelo;

-- ============================================
-- IMAGENS_CARROS
-- ============================================

--Guilherme
CREATE OR REPLACE VIEW vw_imagens_carros_galeria AS
SELECT
    ic.imagem_id,
    ic.carro_id,
    ic.blob_name,
    fn_gerar_url_imagem(ic.blob_name) AS url_imagem,
    ic.descricao,
    ic.ordem,
    ic.is_capa,
    ic.created_at
FROM imagens_carros ic
ORDER BY ic.carro_id, ic.is_capa DESC, ic.ordem;

-- ============================================
-- RESERVAS
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_reservas_detalhes AS
SELECT
    r.reserva_id,
    r.data_reserva,
    r.estado AS estado_reserva,
    r.cliente_id,
    cli.c_nome AS cliente_nome,
    cli.c_email AS cliente_email,
    r.carro_id,
    car.modelo AS carro_modelo,
    car.marca_id AS carro_marca_id,
    car.ano AS carro_ano,
    car.preço AS carro_preco,
    car.status_disponibilidade
FROM reservas r
JOIN clientes cli ON cli.cliente_id = r.cliente_id
JOIN carros car ON car.carro_id = r.carro_id;

-- ============================================
-- FUNCIONARIOS
-- ============================================

--Tiago
CREATE OR REPLACE VIEW vw_funcionarios_vendas AS
SELECT
    v.venda_id,
    v.data,
    f.funcionario_id,
    f.f_nome AS funcionario,
    f.cargo,
    c.c_nome AS cliente,
    ca.modelo AS carro,
    m.m_nome AS marca,
    v.preco_final
FROM vendas v
INNER JOIN funcionarios f ON v.funcionario_id = f.funcionario_id
INNER JOIN clientes c ON v.cliente_id = c.cliente_id
INNER JOIN carros ca ON v.carro_id = ca.carro_id
INNER JOIN marcas m ON ca.marca_id = m.marca_id
ORDER BY v.data DESC;

-- ============================================
-- STANDS
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_stands_oficina AS
SELECT
    s.stand_id,
    s.nome,
    s.localizacao,
    s.contacto,
    s.email,
    s.capacidade_oficina,
    COUNT(b.baia_id) AS total_baias,
    COUNT(CASE WHEN b.status = 'disponivel' THEN 1 END) AS baias_disponiveis
FROM stands s
LEFT JOIN baias_oficina b ON s.stand_id = b.stand_id
WHERE s.capacidade_oficina > 0
GROUP BY s.stand_id, s.nome, s.localizacao, s.contacto, s.email, s.capacidade_oficina;

-- ============================================
-- MECANICOS
-- ============================================

--Tiago
CREATE OR REPLACE VIEW vw_mecanicos_disponibilidade AS
SELECT
    m.mecanico_id,
    m.nome,
    m.especialidade,
    m.telefone,
    m.stand_id,
    s.nome AS stand_nome,
    COUNT(os.ordem_servico_id) AS os_em_andamento
FROM mecanicos m
LEFT JOIN stands s ON m.stand_id = s.stand_id
LEFT JOIN ordens_servico os ON m.mecanico_id = os.mecanico_id AND os.status IN ('aguardando', 'em_andamento')
GROUP BY m.mecanico_id, m.nome, m.especialidade, m.telefone, m.stand_id, s.nome;

-- ============================================
-- ORDENS_SERVICO
-- ============================================

--Guilherme
CREATE OR REPLACE VIEW vw_ordem_servico_detalhes AS
SELECT
    os.ordem_servico_id,
    os.cliente_id,
    c.c_nome,
    os.nome_veiculo,
    ts.nome AS tipo_servico,
    os.mecanico_id,
    m.nome AS mecanico_nome,
    os.baia_id,
    b.numero_baia,
    os.data_entrada,
    os.data_prevista_saida,
    os.data_saida,
    os.status,
    os.prioridade,
    os.descricao_problema,
    os.descricao_solucao,
    os.valor_total,
    os.valor_mao_obra,
    os.valor_pecas,
    os.observacoes,
    os.criado_por_id,
    CASE
        WHEN u.role = 'admin' THEN a.nome
        WHEN u.role = 'gerente' THEN g.nome
        WHEN u.role = 'funcionario' THEN f.f_nome
        WHEN u.role = 'mecanico' THEN m_u.nome
        WHEN u.role = 'cliente' THEN c_u.c_nome
        ELSE 'Sistema'
    END AS criado_por_nome
FROM ordens_servico os
JOIN clientes c ON os.cliente_id = c.cliente_id
JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
LEFT JOIN mecanicos m ON os.mecanico_id = m.mecanico_id
LEFT JOIN baias_oficina b ON os.baia_id = b.baia_id
LEFT JOIN utilizadores u ON os.criado_por_id = u.user_id
LEFT JOIN admins a ON u.admin_id = a.admin_id
LEFT JOIN gerentes g ON u.gerente_id = g.gerente_id
LEFT JOIN funcionarios f ON u.funcionario_id = f.funcionario_id
LEFT JOIN mecanicos m_u ON u.mecanico_id = m_u.mecanico_id
LEFT JOIN clientes c_u ON u.cliente_id = c_u.cliente_id;


--Guilherme
CREATE OR REPLACE VIEW vw_os_em_andamento AS
SELECT
    os.ordem_servico_id,
    os.data_entrada,
    os.data_prevista_saida,
    os.status,
    os.prioridade,
    c.c_nome AS cliente,
    os.nome_veiculo AS carro,
    m.nome AS mecanico,
    ts.nome AS tipo_servico,
    os.valor_total
FROM ordens_servico os
INNER JOIN clientes c ON os.cliente_id = c.cliente_id
LEFT JOIN mecanicos m ON os.mecanico_id = m.mecanico_id
LEFT JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
WHERE os.status NOT IN ('concluida', 'cancelada');

--Tiago
CREATE OR REPLACE VIEW vw_os_atrasadas AS
SELECT
    os.ordem_servico_id,
    os.data_entrada,
    os.data_prevista_saida,
    os.status,
    os.prioridade,
    c.c_nome AS cliente,
    os.nome_veiculo AS carro,
    m.nome AS mecanico,
    ts.nome AS tipo_servico,
    CURRENT_DATE - os.data_prevista_saida AS dias_atraso
FROM ordens_servico os
INNER JOIN clientes c ON os.cliente_id = c.cliente_id
LEFT JOIN mecanicos m ON os.mecanico_id = m.mecanico_id
LEFT JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
WHERE os.data_prevista_saida < CURRENT_DATE AND os.status NOT IN ('concluida', 'cancelada');

--Tiago
CREATE OR REPLACE VIEW vw_ordens_servico_concluidas AS
SELECT 
    os.ordem_servico_id,
    ts.nome AS tipo_servico,
    os.nome_veiculo AS carro_info,
    os.data_entrada,
    os.status
FROM ordens_servico os
JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
WHERE os.status = 'concluido';

-- ============================================
-- BAIAS_OFICINA
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_baias_disponiveis AS
SELECT
    b.baia_id,
    b.stand_id,
    s.nome AS stand_nome,
    b.numero_baia,
    b.tipo,
    b.status
FROM baias_oficina b
INNER JOIN stands s ON b.stand_id = s.stand_id
WHERE b.status = 'disponivel';

-- ============================================
-- PECAS_ACESSORIOS
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_pecas_stock_baixo AS
SELECT
    p.peca_id,
    p.nome,
    p.codigo_fabricante,
    p.preço AS preco,
    p.stock_atual,
    p.stock_minimo,
    GREATEST(p.stock_minimo - p.stock_atual, 0) AS faltam
FROM pecas_acessorios p
WHERE p.stock_atual < p.stock_minimo;

-- ============================================
-- SERVICO_PEÇAS
-- ============================================

--Lucas
CREATE OR REPLACE VIEW vw_servico_pecas AS
SELECT
    sp.ordem_servico_id,
    sp.peca_id,
    p.nome AS peca_nome,
    sp.quantidade,
    sp.preco_unitario,
    sp.preco_total
FROM servico_pecas sp
JOIN pecas_acessorios p ON sp.peca_id = p.peca_id
ORDER BY sp.ordem_servico_id, p.nome;

-- ============================================
-- CLIENTES
-- ============================================

CREATE OR REPLACE VIEW vw_clientes_detalhes AS
SELECT
    c.cliente_id,
    c.c_nome,
    c.c_email,
    c.c_telefone,
    c.nif,
    c.data_cadastro,
    c.data_nascimento,
    COUNT(v.venda_id) AS total_vendas,
    COALESCE(SUM(v.preco_final), 0) AS valor_total
FROM clientes c
LEFT JOIN vendas v ON c.cliente_id = v.cliente_id
GROUP BY c.cliente_id, c.c_nome, c.c_email, c.c_telefone, c.nif, c.data_cadastro, c.data_nascimento
ORDER BY c.c_nome;

-- ============================================
-- VIEWS MATERIALIZADAS
-- ============================================

--Guilherme 
CREATE MATERIALIZED VIEW vw_clientes_compras AS
SELECT
    c.cliente_id,
    c.c_nome,
    c.c_email,
    COUNT(v.venda_id) AS total_vendas,
    COALESCE(SUM(v.preco_final), 0) AS valor_total
FROM clientes c
LEFT JOIN vendas v ON c.cliente_id = v.cliente_id
GROUP BY c.cliente_id, c.c_nome, c.c_email;

-- ============================================
-- AVALIACOES
-- ============================================

--Tiago
CREATE MATERIALIZED VIEW vw_avaliacoes_carros AS
SELECT
    a.carro_id,
    COUNT(a.avaliacao_id) AS total_avaliacoes,
    ROUND(AVG(a.classificacao)::numeric, 2) AS media_classificacao,
    MIN(a.classificacao) AS classificacao_minima,
    MAX(a.classificacao) AS classificacao_maxima,
    COUNT(CASE WHEN a.comentario IS NOT NULL AND a.comentario != '' THEN 1 END) AS avaliacoes_com_comentario,
    MAX(a.data_avaliacao) AS ultima_avaliacao
FROM avaliacoes a
WHERE a.tipo_avaliacao = 'venda' AND a.carro_id IS NOT NULL
GROUP BY a.carro_id
ORDER BY media_classificacao DESC, total_avaliacoes DESC;

--Tiago
CREATE MATERIALIZED VIEW vw_avaliacoes_servicos AS
SELECT
    a.ordem_servico_id,
    COUNT(a.avaliacao_id) AS total_avaliacoes,
    ROUND(AVG(a.classificacao)::numeric, 2) AS media_classificacao,
    MIN(a.classificacao) AS classificacao_minima,
    MAX(a.classificacao) AS classificacao_maxima,
    COUNT(CASE WHEN a.comentario IS NOT NULL AND a.comentario != '' THEN 1 END) AS avaliacoes_com_comentario,
    MAX(a.data_avaliacao) AS ultima_avaliacao
FROM avaliacoes a
WHERE a.tipo_avaliacao = 'servico' AND a.ordem_servico_id IS NOT NULL
GROUP BY a.ordem_servico_id
ORDER BY media_classificacao DESC, total_avaliacoes DESC;

-- ============================================
-- FUNCIONARIOS
-- ============================================

--Guilherme
CREATE MATERIALIZED VIEW vw_funcionarios_desempenho AS
SELECT
    f.funcionario_id,
    f.f_nome AS funcionario,
    f.cargo,
    f.stand_id,
    s.nome AS stand_nome,
    COUNT(v.venda_id) AS total_vendas,
    COALESCE(SUM(v.preco_final), 0) AS valor_total_vendas,
    ROUND(AVG(v.preco_final)::numeric, 2) AS media_venda
FROM funcionarios f
LEFT JOIN stands s ON f.stand_id = s.stand_id
LEFT JOIN vendas v ON f.funcionario_id = v.funcionario_id
GROUP BY f.funcionario_id, f.f_nome, f.cargo, f.stand_id, s.nome;

-- ============================================
-- STANDS
-- ============================================

--Guilherme
CREATE MATERIALIZED VIEW vw_stock_atual AS
SELECT
    s.stand_id,
    s.nome AS stand,
    COUNT(c.carro_id) AS total_carros,
    COUNT(CASE WHEN c.status_disponibilidade = 'disponivel' THEN 1 END) AS disponiveis,
    COUNT(CASE WHEN c.status_disponibilidade = 'reservado' THEN 1 END) AS reservados,
    COUNT(CASE WHEN c.status_disponibilidade = 'vendido' THEN 1 END) AS vendidos
FROM stands s
LEFT JOIN carros c ON s.stand_id = c.stand_id
GROUP BY s.stand_id, s.nome;

-- ============================================
-- MECANICOS
-- ============================================

--Guilherme
CREATE MATERIALIZED VIEW vw_mecanicos_desempenho AS
SELECT
    m.mecanico_id,
    m.nome,
    m.especialidade,
    m.stand_id,
    s.nome AS stand_nome,
    COUNT(os.ordem_servico_id) AS total_os_concluidas,
    COALESCE(SUM(os.valor_total), 0) AS valor_total_servicos,
    ROUND(AVG(os.valor_total)::numeric, 2) AS media_valor_servico,
    ROUND(AVG(EXTRACT(EPOCH FROM (os.data_saida::timestamp - os.data_entrada::timestamp)) / 3600)::numeric, 2) AS media_horas_servico
FROM mecanicos m
LEFT JOIN stands s ON m.stand_id = s.stand_id
LEFT JOIN ordens_servico os ON m.mecanico_id = os.mecanico_id AND os.status = 'concluida'
GROUP BY m.mecanico_id, m.nome, m.especialidade, m.stand_id, s.nome;

-- ============================================
-- TIPOS_SERVICO
-- ============================================

--Lucas
CREATE MATERIALIZED VIEW vw_servicos_mais_vendidos AS
SELECT
    ts.tipo_servico_id,
    ts.nome,
    COUNT(os.ordem_servico_id) AS total_servicos,
    COALESCE(SUM(COALESCE(os.valor_mao_obra, 0) + COALESCE(os.valor_pecas, 0)), 0)::DECIMAL(12,2) AS faturacao_total
FROM tipos_servico ts
LEFT JOIN ordens_servico os ON os.tipo_servico_id = ts.tipo_servico_id
GROUP BY ts.tipo_servico_id, ts.nome
ORDER BY total_servicos DESC;

-- ============================================
-- INDEXES PARA VIEWS MATERIALIZADAS
-- ============================================

CREATE UNIQUE INDEX idx_vw_clientes_compras_pk ON vw_clientes_compras(cliente_id);
CREATE INDEX idx_vw_clientes_compras_valor ON vw_clientes_compras(valor_total DESC);

CREATE UNIQUE INDEX idx_vw_avaliacoes_carros_pk ON vw_avaliacoes_carros(carro_id);
CREATE INDEX idx_vw_avaliacoes_carros_media ON vw_avaliacoes_carros(media_classificacao DESC);

CREATE UNIQUE INDEX idx_vw_avaliacoes_servicos_pk ON vw_avaliacoes_servicos(ordem_servico_id);
CREATE INDEX idx_vw_avaliacoes_servicos_media ON vw_avaliacoes_servicos(media_classificacao DESC);

CREATE UNIQUE INDEX idx_vw_funcionarios_desempenho_pk ON vw_funcionarios_desempenho(funcionario_id);

CREATE UNIQUE INDEX idx_vw_stock_atual_pk ON vw_stock_atual(stand_id);
CREATE INDEX idx_vw_stock_atual_disponiveis ON vw_stock_atual(disponiveis DESC);

CREATE UNIQUE INDEX idx_vw_mecanicos_desempenho_pk ON vw_mecanicos_desempenho(mecanico_id);

CREATE UNIQUE INDEX idx_vw_servicos_mais_vendidos_pk ON vw_servicos_mais_vendidos(tipo_servico_id);
CREATE INDEX idx_vw_servicos_mais_vendidos_faturacao ON vw_servicos_mais_vendidos(faturacao_total DESC);

