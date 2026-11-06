-- ============================================
-- Inserts
-- ============================================
    
-- Estas tabelas não têm CRUD no Frontend

-- ============================================
-- MARCAS DE CARROS
-- ============================================
INSERT INTO marcas (m_nome, país_origem) VALUES
('Audi', 'Alemanha'),
('BMW', 'Alemanha'),
('Mercedes-Benz', 'Alemanha'),
('Volkswagen', 'Alemanha'),
('Porsche', 'Alemanha'),
('Opel', 'Alemanha'),
('Toyota', 'Japão'),
('Honda', 'Japão'),
('Nissan', 'Japão'),
('Mazda', 'Japão'),
('Mitsubishi', 'Japão'),
('Suzuki', 'Japão'),
('Lexus', 'Japão'),
('Ford', 'Estados Unidos'),
('Chevrolet', 'Estados Unidos'),
('Tesla', 'Estados Unidos'),
('Jeep', 'Estados Unidos'),
('Dodge', 'Estados Unidos'),
('Peugeot', 'França'),
('Renault', 'França'),
('Citroën', 'França'),
('DS', 'França'),
('Fiat', 'Itália'),
('Alfa Romeo', 'Itália'),
('Ferrari', 'Itália'),
('Lamborghini', 'Itália'),
('Maserati', 'Itália'),
('SEAT', 'Espanha'),
('Cupra', 'Espanha'),
('Volvo', 'Suécia'),
('Hyundai', 'Coreia do Sul'),
('Kia', 'Coreia do Sul'),
('Land Rover', 'Reino Unido'),
('Jaguar', 'Reino Unido'),
('Mini', 'Reino Unido'),
('Skoda', 'República Checa'),
('Dacia', 'Roménia'),
('BYD', 'China'),
('MG', 'China')
ON CONFLICT DO NOTHING;

-- ============================================
-- TIPOS DE SERVIÇO
-- ============================================
INSERT INTO tipos_servico (nome, descricao, tempo_estimado, preco_base) VALUES
('Mudança de Óleo', 'Substituição de óleo do motor e filtro', 30, 45.00),
('Revisão Completa', 'Revisão geral com verificação de todos os sistemas', 120, 150.00),
('Alinhamento e Balanceamento', 'Alinhamento de direção e balanceamento de rodas', 60, 60.00),
('Troca de Pastilhas de Travão', 'Substituição de pastilhas dianteiras ou traseiras', 45, 80.00),
('Troca de Discos de Travão', 'Substituição de discos de travão', 90, 120.00),
('Mudança de Pneus', 'Troca de pneus (mão de obra, pneus não incluídos)', 40, 40.00),
('Diagnóstico Eletrónico', 'Leitura de códigos de erro e diagnóstico', 30, 35.00),
('Troca de Bateria', 'Substituição de bateria do veículo', 20, 25.00),
('Troca de Correia de Distribuição', 'Substituição da correia de distribuição', 180, 200.00),
('Troca de Embraiagem', 'Substituição do kit de embraiagem', 300, 350.00),
('Reparação de Ar Condicionado', 'Diagnóstico e reparação do sistema A/C', 90, 85.00),
('Carga de Ar Condicionado', 'Recarga de gás do ar condicionado', 45, 55.00),
('Troca de Amortecedores', 'Substituição de amortecedores (par)', 120, 100.00),
('Troca de Velas de Ignição', 'Substituição das velas de ignição', 45, 40.00),
('Limpeza de Injetores', 'Limpeza do sistema de injeção', 60, 70.00),
('Troca de Filtro de Ar', 'Substituição do filtro de ar', 15, 20.00),
('Troca de Filtro de Habitáculo', 'Substituição do filtro do habitáculo', 15, 20.00),
('Inspeção Pré-IPO', 'Verificação prévia à inspeção obrigatória', 60, 45.00),
('Polimento e Vitrificação', 'Tratamento estético da pintura', 240, 180.00),
('Lavagem Completa', 'Lavagem interior e exterior detalhada', 90, 50.00)
ON CONFLICT DO NOTHING;

-- ============================================
-- PEÇAS E ACESSÓRIOS COMUNS
-- ============================================
INSERT INTO pecas_acessorios (nome, descricao, codigo_fabricante, preço, stock_atual, stock_minimo) VALUES
-- Filtros
('Filtro de Óleo Universal', 'Filtro de óleo compatível com múltiplas marcas', 'FO-UNI-001', 12.50, 50, 10),
('Filtro de Ar Universal', 'Filtro de ar para motores a gasolina', 'FA-UNI-001', 15.00, 40, 8),
('Filtro de Habitáculo', 'Filtro de pólen para ar condicionado', 'FH-UNI-001', 18.00, 35, 5),
('Filtro de Combustível Gasolina', 'Filtro de combustível para motores a gasolina', 'FC-GAS-001', 22.00, 25, 5),
('Filtro de Combustível Diesel', 'Filtro de combustível para motores diesel', 'FC-DIE-001', 28.00, 20, 5),

-- Óleos
('Óleo Motor 5W30 Sintético 5L', 'Óleo sintético alta performance', 'OL-5W30-5L', 45.00, 30, 10),
('Óleo Motor 5W40 Sintético 5L', 'Óleo sintético para motores exigentes', 'OL-5W40-5L', 48.00, 25, 8),
('Óleo Motor 10W40 Semi-Sintético 5L', 'Óleo semi-sintético uso geral', 'OL-10W40-5L', 35.00, 35, 10),
('Óleo Travões DOT4 1L', 'Fluido de travões DOT4', 'OL-DOT4-1L', 12.00, 20, 5),
('Óleo Direção Assistida 1L', 'Fluido para direção assistida', 'OL-DIR-1L', 15.00, 15, 3),

-- Travões
('Pastilhas Travão Dianteiras', 'Jogo de pastilhas dianteiras universais', 'PT-DIA-001', 35.00, 20, 5),
('Pastilhas Travão Traseiras', 'Jogo de pastilhas traseiras universais', 'PT-TRA-001', 30.00, 18, 5),
('Disco Travão Dianteiro', 'Disco de travão dianteiro ventilado', 'DT-DIA-001', 55.00, 12, 4),
('Disco Travão Traseiro', 'Disco de travão traseiro sólido', 'DT-TRA-001', 45.00, 10, 4),

-- Iluminação
('Lâmpada H7 55W', 'Lâmpada halogéneo H7', 'LAM-H7-55', 8.00, 40, 10),
('Lâmpada H4 60/55W', 'Lâmpada halogéneo H4', 'LAM-H4-60', 10.00, 35, 8),
('Lâmpada LED H7', 'Lâmpada LED H7 6000K', 'LAM-H7-LED', 35.00, 20, 5),
('Lâmpada LED H4', 'Lâmpada LED H4 6000K', 'LAM-H4-LED', 40.00, 18, 5),

-- Velas e Ignição
('Vela de Ignição NGK', 'Vela de ignição standard', 'VEL-NGK-001', 6.50, 60, 15),
('Vela de Ignição Iridium', 'Vela de ignição alta performance', 'VEL-IRI-001', 18.00, 25, 8),
('Bobina de Ignição', 'Bobina de ignição universal', 'BOB-IGN-001', 45.00, 10, 3),

-- Correias
('Correia Alternador', 'Correia poly-v alternador', 'COR-ALT-001', 22.00, 15, 4),
('Correia Distribuição Kit', 'Kit completo correia distribuição', 'COR-DIS-KIT', 85.00, 8, 3),
('Tensor Correia', 'Tensor de correia automático', 'TEN-COR-001', 35.00, 10, 3),

-- Suspensão
('Amortecedor Dianteiro', 'Amortecedor dianteiro standard', 'AMO-DIA-001', 75.00, 8, 2),
('Amortecedor Traseiro', 'Amortecedor traseiro standard', 'AMO-TRA-001', 65.00, 8, 2),
('Mola Suspensão Dianteira', 'Mola helicoidal dianteira', 'MOL-DIA-001', 55.00, 6, 2),

-- Bateria
('Bateria 60Ah', 'Bateria arranque 60Ah 540A', 'BAT-60AH', 85.00, 10, 3),
('Bateria 70Ah', 'Bateria arranque 70Ah 640A', 'BAT-70AH', 95.00, 8, 3),
('Bateria 80Ah', 'Bateria arranque 80Ah 740A', 'BAT-80AH', 110.00, 6, 2),

-- Limpeza
('Escovas Limpa-Vidros Par', 'Par de escovas limpa-vidros universais', 'ESC-LV-PAR', 18.00, 25, 5),
('Líquido Limpa-Vidros 5L', 'Líquido limpa para-brisas', 'LIQ-LV-5L', 8.00, 30, 8),
('Anticongelante 5L', 'Líquido refrigerante -35°C', 'ANT-CON-5L', 15.00, 20, 5)
ON CONFLICT DO NOTHING;

-- ============================================
-- STANDS (Exemplo)
-- ============================================
INSERT INTO stands (nome, localizacao, contacto, email, capacidade_oficina) VALUES
('Auto Care Lisboa', 'Av. da Liberdade 245, Lisboa', '+351 21 123 4567', 'lisboa@autocare.pt', 10),
('Auto Care Porto', 'Rua de Santa Catarina 150, Porto', '+351 22 987 6543', 'porto@autocare.pt', 8),
('Auto Care Faro', 'Av. 5 de Outubro 88, Faro', '+351 28 555 1234', 'faro@autocare.pt', 5)
ON CONFLICT DO NOTHING;

-- ============================================
-- BAIAS DE OFICINA (para cada stand)
-- ============================================
-- Lisboa (10 baias)
INSERT INTO baias_oficina (stand_id, numero_baia, tipo, status) VALUES
(1, 'L01', 'Manutenção Geral', 'disponivel'),
(1, 'L02', 'Manutenção Geral', 'disponivel'),
(1, 'L03', 'Manutenção Geral', 'disponivel'),
(1, 'L04', 'Mecânica Pesada', 'disponivel'),
(1, 'L05', 'Mecânica Pesada', 'disponivel'),
(1, 'L06', 'Eletricidade', 'disponivel'),
(1, 'L07', 'Eletricidade', 'disponivel'),
(1, 'L08', 'Pneus e Alinhamento', 'disponivel'),
(1, 'L09', 'Lavagem', 'disponivel'),
(1, 'L10', 'Pintura', 'disponivel'),
-- Porto (8 baias)
(2, 'P01', 'Manutenção Geral', 'disponivel'),
(2, 'P02', 'Manutenção Geral', 'disponivel'),
(2, 'P03', 'Mecânica Pesada', 'disponivel'),
(2, 'P04', 'Mecânica Pesada', 'disponivel'),
(2, 'P05', 'Eletricidade', 'disponivel'),
(2, 'P06', 'Pneus e Alinhamento', 'disponivel'),
(2, 'P07', 'Lavagem', 'disponivel'),
(2, 'P08', 'Pintura', 'disponivel'),
-- Faro (5 baias)
(3, 'F01', 'Manutenção Geral', 'disponivel'),
(3, 'F02', 'Manutenção Geral', 'disponivel'),
(3, 'F03', 'Mecânica Pesada', 'disponivel'),
(3, 'F04', 'Pneus e Alinhamento', 'disponivel'),
(3, 'F05', 'Lavagem', 'disponivel')
ON CONFLICT DO NOTHING;

-- ============================================
-- EQUIPAMENTOS (Exemplo por stand)
-- ============================================
INSERT INTO equipamentos (stand_id, nome, tipo, fabricante, data_aquisicao, valor_aquisicao, proxima_manutencao, status) VALUES
-- Lisboa
(1, 'Elevador Hidráulico 4T', 'Elevador', 'Ravaglioli', '2023-01-15', 8500.00, '2026-01-15', 'operacional'),
(1, 'Elevador Hidráulico 4T #2', 'Elevador', 'Ravaglioli', '2023-01-15', 8500.00, '2026-01-15', 'operacional'),
(1, 'Scanner OBD-II Pro', 'Diagnóstico', 'Bosch', '2024-03-10', 3200.00, '2026-03-10', 'operacional'),
(1, 'Máquina Alinhamento 3D', 'Alinhamento', 'Hunter', '2023-06-20', 15000.00, '2026-06-20', 'operacional'),
(1, 'Equilibradora de Rodas', 'Pneus', 'Corghi', '2023-06-20', 4500.00, '2026-06-20', 'operacional'),
(1, 'Compressor 500L', 'Ar Comprimido', 'Atlas Copco', '2022-09-01', 2800.00, '2025-09-01', 'operacional'),
-- Porto
(2, 'Elevador Hidráulico 3.5T', 'Elevador', 'Ravaglioli', '2023-05-10', 7200.00, '2026-05-10', 'operacional'),
(2, 'Scanner OBD-II', 'Diagnóstico', 'Autel', '2024-01-20', 1800.00, '2026-01-20', 'operacional'),
(2, 'Máquina Alinhamento', 'Alinhamento', 'Corghi', '2024-02-15', 9000.00, '2027-02-15', 'operacional'),
(2, 'Compressor 300L', 'Ar Comprimido', 'Fini', '2023-03-01', 1500.00, '2025-03-01', 'operacional'),
-- Faro
(3, 'Elevador Hidráulico 3T', 'Elevador', 'Werther', '2024-01-10', 5500.00, '2027-01-10', 'operacional'),
(3, 'Scanner OBD-II Básico', 'Diagnóstico', 'Launch', '2024-06-15', 800.00, '2026-06-15', 'operacional'),
(3, 'Compressor 200L', 'Ar Comprimido', 'Fini', '2024-01-10', 900.00, '2026-01-10', 'operacional')
ON CONFLICT DO NOTHING;

-- ============================================
-- FORNECEDORES (Exemplo)
-- ============================================
INSERT INTO fornecedores (f_nome, f_contacto, f_email, tipo) VALUES
('Auto Peças Nacional', '+351 21 111 2222', 'geral@autopecas.pt', 'pecas'),
('Import Cars Europe', '+351 21 333 4444', 'vendas@importcars.eu', 'carros'),
('Lubricantes Ibéricos', '+351 21 555 6666', 'comercial@lubricantes.pt', 'pecas'),
('Premium Motors', '+351 22 777 8888', 'fleet@premiummotors.pt', 'carros'),
('Total Parts Distribution', '+351 21 999 0000', 'orders@totalparts.pt', 'ambos'),
('Bosch Service Partner', '+351 21 222 3333', 'parceiros@bosch.pt', 'pecas'),
('Mann+Hummel Portugal', '+351 21 444 5555', 'filtros@mann-hummel.pt', 'pecas')
ON CONFLICT DO NOTHING;


