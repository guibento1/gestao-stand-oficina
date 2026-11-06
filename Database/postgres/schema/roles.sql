-- ============================================
-- PostgreSQL - ROLES E PERMISSÕES
-- Sistema de Stand e Oficina
-- ============================================

-- ROLE: GERENTE (Acesso quase completo)
CREATE ROLE role_gerente LOGIN PASSWORD 'gerente';

GRANT CONNECT ON DATABASE "bdII_25193" TO role_gerente;
GRANT USAGE ON SCHEMA public TO role_gerente;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_gerente;

GRANT INSERT, UPDATE, DELETE ON
    carros, clientes, funcionarios, mecanicos,
    reservas, vendas, ordens_servico, avaliacoes,
    imagens_carros, baias_oficina, servico_pecas
TO role_gerente;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO role_gerente;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO role_gerente;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO role_gerente;

-- ROLE: FUNCIONARIO (Vendas e Atendimento)
CREATE ROLE role_funcionario LOGIN PASSWORD 'funcionario';

GRANT CONNECT ON DATABASE "bdII_25193" TO role_funcionario;
GRANT USAGE ON SCHEMA public TO role_funcionario;

GRANT SELECT ON
    stands, marcas, carros, clientes,
    funcionarios, pecas_acessorios, tipos_servico,
    reservas, vendas, imagens_carros,
    ordens_servico, baias_oficina, servico_pecas
TO role_funcionario;

GRANT INSERT, UPDATE ON
    clientes, reservas, vendas
TO role_funcionario;

GRANT UPDATE (status_disponibilidade) ON carros TO role_funcionario;

GRANT USAGE, SELECT ON
    clientes_cliente_id_seq, reservas_reserva_id_seq, vendas_venda_id_seq
TO role_funcionario;

-- ROLE: MECANICO (Oficina)
CREATE ROLE role_mecanico LOGIN PASSWORD 'mecanico';

GRANT CONNECT ON DATABASE "bdII_25193" TO role_mecanico;
GRANT USAGE ON SCHEMA public TO role_mecanico;

GRANT SELECT ON
    stands, marcas, carros, clientes, mecanicos,
    tipos_servico, pecas_acessorios,
    baias_oficina, ordens_servico, imagens_carros, servico_pecas
TO role_mecanico;

GRANT INSERT, UPDATE ON
    ordens_servico
TO role_mecanico;

GRANT INSERT, UPDATE ON
    servico_pecas
TO role_mecanico;

GRANT UPDATE (status_disponibilidade) ON carros TO role_mecanico;
GRANT UPDATE (status) ON baias_oficina TO role_mecanico;

GRANT USAGE, SELECT ON
    ordens_servico_ordem_servico_id_seq
TO role_mecanico;

GRANT USAGE, SELECT ON
    servico_pecas_servico_peca_id_seq
TO role_mecanico;

-- ROLE: CLIENTE (Portal - Read-only + ações limitadas)
CREATE ROLE role_cliente LOGIN PASSWORD 'cliente';

GRANT CONNECT ON DATABASE "bdII_25193" TO role_cliente;
GRANT USAGE ON SCHEMA public TO role_cliente;

GRANT SELECT ON
    stands, marcas, carros, imagens_carros,
    tipos_servico, pecas_acessorios
TO role_cliente;

GRANT INSERT ON reservas, avaliacoes TO role_cliente;

GRANT USAGE ON
    reservas_reserva_id_seq,
    avaliacoes_avaliacao_id_seq
TO role_cliente;