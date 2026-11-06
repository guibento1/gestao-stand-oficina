CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Adiconado stand porquê o stand é obrigatório para várias tabelas
INSERT INTO stands (nome, localizacao, contacto, email, capacidade_oficina) VALUES
('Stand Principal', 'Lisboa', '211234567', 'stand.lisboa@stand.com', 30);

INSERT INTO admins (nome, email, telefone, departamento, ativo) VALUES
('Cristiano Ronaldo', 'cristiano.ronaldo@email.com', '912345678', 'Diretor', true);
INSERT INTO gerentes (stand_id, nome, email, telefone, departamento) VALUES
(1, 'Paulo Castro', 'paulo.castro@email.com', '912345679', 'Vendas');
INSERT INTO funcionarios (stand_id, cargo, f_nome, f_email, f_telefone) VALUES
(1, 'Vendedor', 'Joao Silva', 'joao.silva@email.com', '912345680');
INSERT INTO mecanicos (stand_id, nome, especialidade, telefone, email) VALUES
(1, 'Carlos Santos', 'Mecanica Geral', '912345681', 'carlos.santos@email.com');
INSERT INTO clientes (c_nome, c_email, c_telefone, nif) VALUES
('Maria Oliveira', 'maria.oliveira@email.com', '912345682', '12345678901');

INSERT INTO utilizadores (email, password_hash, role, admin_id, gerente_id, funcionario_id, mecanico_id, cliente_id, ativo, created_at) VALUES
-- ADMIN
('cristiano.ronaldo@email.com', crypt('cristianoronaldo', gen_salt('bf', 10)), 'admin', 1, NULL, NULL, NULL, NULL, true, NOW()),
-- GERENTE
('paulo.castro@email.com', crypt('paulocastro', gen_salt('bf', 10)), 'gerente', NULL, 1, NULL, NULL, NULL, true, NOW()),
-- FUNCIONARIO
('joao.silva@email.com', crypt('joaosilva', gen_salt('bf', 10)), 'funcionario', NULL, NULL, 1, NULL, NULL, true, NOW()),
-- MECANICO
('carlos.santos@email.com', crypt('carlossantos', gen_salt('bf', 10)), 'mecanico', NULL, NULL, NULL, 1, NULL, true, NOW()),
-- CLIENTE
('maria.oliveira@email.com', crypt('mariaoliveira', gen_salt('bf', 10)), 'cliente', NULL, NULL, NULL, NULL, 1, true, NOW());
