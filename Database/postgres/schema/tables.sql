-- ============================================
-- PostgreSQL 9.x - Sistema de Stand e Oficina (Versão Filtrada)
-- ============================================

-- ============================================
-- DROP TABLES (Apenas as que serão mantidas)
-- ============================================

DROP TABLE IF EXISTS imagens_carros CASCADE;
DROP TABLE IF EXISTS carros CASCADE;
DROP TABLE IF EXISTS marcas CASCADE;
DROP TABLE IF EXISTS stands CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS utilizadores CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS gerentes CASCADE;
DROP TABLE IF EXISTS funcionarios CASCADE;
DROP TABLE IF EXISTS mecanicos CASCADE;
DROP TABLE IF EXISTS vendas CASCADE;
DROP TABLE IF EXISTS reservas CASCADE;
DROP TABLE IF EXISTS avaliacoes CASCADE;
DROP TABLE IF EXISTS pecas_acessorios CASCADE;
DROP TABLE IF EXISTS tipos_servico CASCADE;
DROP TABLE IF EXISTS ordens_servico CASCADE;
DROP TABLE IF EXISTS baias_oficina CASCADE;
DROP TABLE IF EXISTS servico_pecas CASCADE;

-- Stands
CREATE TABLE stands (
   stand_id        SERIAL PRIMARY KEY,
   nome            VARCHAR(150) NOT NULL,
   localizacao     VARCHAR(150) NOT NULL,
   contacto        VARCHAR(20) NOT NULL,
   email           VARCHAR(100),
   capacidade_oficina INT DEFAULT 0
);

-- Marcas
CREATE TABLE marcas (
   marca_id        SERIAL PRIMARY KEY,
   país_origem     VARCHAR(50) NOT NULL,
   m_nome          VARCHAR(100) NOT NULL
);

-- Peças e Acessórios
CREATE TABLE pecas_acessorios (
   peca_id         SERIAL PRIMARY KEY,
   nome            VARCHAR(150) NOT NULL,
   descricao       TEXT,
   codigo_fabricante VARCHAR(50),
   preço           DECIMAL(10,2) NOT NULL,
   stock_atual     INT NOT NULL DEFAULT 0,
   stock_minimo    INT NOT NULL DEFAULT 0
);

-- Tipos de Serviço
CREATE TABLE tipos_servico (
   tipo_servico_id SERIAL PRIMARY KEY,
   nome            VARCHAR(100) NOT NULL,
   descricao       TEXT,
   tempo_estimado  INT NOT NULL,
   preco_base      DECIMAL(10,2) NOT NULL
);

-- Carros
CREATE TABLE carros (
   carro_id        SERIAL PRIMARY KEY,
   stand_id        INT NOT NULL,
   marca_id        INT NOT NULL,
   modelo          VARCHAR(100) NOT NULL,
   ano             INT NOT NULL,
   preço           DECIMAL(10,2) NOT NULL,
   estado          VARCHAR(20) NOT NULL CHECK (estado IN ('novo', 'usado', 'seminovo')),
   quilometragem   INT DEFAULT 0,
   cor             VARCHAR(50),
   chassi          VARCHAR(50) UNIQUE,
   placa           VARCHAR(20) UNIQUE,
   status_disponibilidade VARCHAR(20) DEFAULT 'disponivel' CHECK (status_disponibilidade IN ('disponivel', 'reservado', 'vendido', 'em_manutencao')),
   data_aquisicao  DATE,
   combustivel     VARCHAR(20) CHECK (combustivel IN ('gasolina', 'diesel', 'eletrico', 'hibrido', 'gpl')),
   potencia        INT,
   cilindrada      INT,
   portas          INT,
   lugares         INT,
   ref_imagem_capa VARCHAR(500),
   CONSTRAINT FK_CARROS_MARCA FOREIGN KEY (marca_id)
      REFERENCES marcas (marca_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
   CONSTRAINT FK_CARROS_STAND FOREIGN KEY (stand_id)
      REFERENCES stands (stand_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- Imagens Carros
-- Nota: Depende de utilizadores (criada abaixo)
CREATE TABLE imagens_carros (
    imagem_id SERIAL PRIMARY KEY,
    carro_id INT NOT NULL,
    blob_name VARCHAR(255) NOT NULL,
    descricao VARCHAR(200),
    ordem INT DEFAULT 0,
    is_capa BOOLEAN DEFAULT FALSE,
    uploaded_by INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT FK_IMAGENSCARROS_CARRO FOREIGN KEY (carro_id)
        REFERENCES carros (carro_id) ON DELETE CASCADE,
    CONSTRAINT chk_imagens_ordem CHECK (ordem >= 0)
);

-- Baias Oficina
CREATE TABLE baias_oficina (
   baia_id         SERIAL PRIMARY KEY,
   stand_id        INT NOT NULL,
   numero_baia     VARCHAR(10) NOT NULL,
   tipo            VARCHAR(50) NOT NULL,
   status          VARCHAR(30) NOT NULL DEFAULT 'disponivel' CHECK (status IN ('disponivel', 'ocupada', 'manutencao')),
   CONSTRAINT FK_BAIAS_STAND FOREIGN KEY (stand_id)
      REFERENCES stands (stand_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
   CONSTRAINT UQ_BAIA_NUMERO UNIQUE (stand_id, numero_baia)
);

-- Funcionários
CREATE TABLE funcionarios (
   funcionario_id  SERIAL PRIMARY KEY,
   stand_id        INT NOT NULL,
   cargo           VARCHAR(50) NOT NULL,
   f_nome          VARCHAR(100) NOT NULL,
   f_email         VARCHAR(100) NOT NULL UNIQUE,
   f_telefone      VARCHAR(20) NOT NULL,
   data_admissao   DATE NOT NULL DEFAULT CURRENT_DATE,
   salario         DECIMAL(10,2),
   data_saida      DATE,
   CONSTRAINT FK_FUNCIONA_EMPREGA_STANDS FOREIGN KEY (stand_id)
      REFERENCES stands (stand_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- Gerentes
CREATE TABLE gerentes (
   gerente_id      SERIAL PRIMARY KEY,
   stand_id        INT NOT NULL,
   nome            VARCHAR(100) NOT NULL,
   email           VARCHAR(100) UNIQUE,
   telefone        VARCHAR(20) NOT NULL,
   departamento    VARCHAR(100),
   data_admissao   DATE NOT NULL DEFAULT CURRENT_DATE,
   salario         DECIMAL(10,2),
   CONSTRAINT FK_GERENTES_STAND FOREIGN KEY (stand_id)
      REFERENCES stands (stand_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- Mecânicos
CREATE TABLE mecanicos (
   mecanico_id     SERIAL PRIMARY KEY,
   stand_id        INT NOT NULL,
   nome            VARCHAR(100) NOT NULL,
   especialidade   VARCHAR(100) NOT NULL,
   telefone        VARCHAR(20) NOT NULL,
   email           VARCHAR(100) UNIQUE,
   data_admissao   DATE NOT NULL DEFAULT CURRENT_DATE,
   salario         DECIMAL(10,2),
   CONSTRAINT FK_MECANICOS_STAND FOREIGN KEY (stand_id)
      REFERENCES stands (stand_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- Admins
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    departamento VARCHAR(50),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT true
);



-- Clientes
CREATE TABLE clientes (
   cliente_id      SERIAL PRIMARY KEY,
   c_nome          VARCHAR(100) NOT NULL,
   c_email         VARCHAR(100) NOT NULL UNIQUE,
   c_telefone      VARCHAR(20),
   nif             VARCHAR(20) UNIQUE,
   data_cadastro   DATE NOT NULL DEFAULT CURRENT_DATE,
   data_nascimento DATE
);


CREATE TABLE utilizadores (
   user_id         SERIAL PRIMARY KEY,
   email           VARCHAR(100) NOT NULL UNIQUE,
   password_hash   VARCHAR(255) NOT NULL,
   role            VARCHAR(20) NOT NULL CHECK (role IN ('gerente', 'funcionario', 'mecanico', 'cliente', 'admin')),
   admin_id        INT,
   gerente_id      INT,
   cliente_id      INT,
   funcionario_id  INT,
   mecanico_id     INT,
   ativo           BOOLEAN NOT NULL DEFAULT TRUE,
   created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
   last_login      TIMESTAMP,
   CONSTRAINT FK_UTILIZADORES_ADMIN FOREIGN KEY (admin_id)
      REFERENCES admins (admin_id) ON DELETE SET NULL,
   CONSTRAINT FK_UTILIZADORES_GERENTE FOREIGN KEY (gerente_id)
      REFERENCES gerentes (gerente_id) ON DELETE SET NULL,
   CONSTRAINT FK_UTILIZADORES_CLIENTE FOREIGN KEY (cliente_id)
      REFERENCES clientes (cliente_id) ON DELETE SET NULL,
   CONSTRAINT FK_UTILIZADORES_FUNCIONARIO FOREIGN KEY (funcionario_id)
      REFERENCES funcionarios (funcionario_id) ON DELETE SET NULL,
   CONSTRAINT FK_UTILIZADORES_MECANICO FOREIGN KEY (mecanico_id)
      REFERENCES mecanicos (mecanico_id) ON DELETE SET NULL
);

ALTER TABLE imagens_carros
ADD CONSTRAINT FK_IMAGENSCARROS_UPLOADED_BY FOREIGN KEY (uploaded_by)
REFERENCES utilizadores (user_id) ON DELETE SET NULL;

-- Serviço Peças
CREATE TABLE servico_pecas (
   servico_peca_id SERIAL PRIMARY KEY,
   ordem_servico_id INT NOT NULL,
   peca_id         INT NOT NULL,
   quantidade      DECIMAL(10,2) NOT NULL,
   preco_unitario  DECIMAL(10,2) NOT NULL,
   preco_total     DECIMAL(10,2) NOT NULL,
   CONSTRAINT FK_SERVICOPECAS_ORDEM_SERVICO FOREIGN KEY (ordem_servico_id)
      REFERENCES ordens_servico (ordem_servico_id) ON DELETE CASCADE,
   CONSTRAINT FK_SERVICOPECAS_PECA FOREIGN KEY (peca_id)
      REFERENCES pecas_acessorios (peca_id) ON DELETE RESTRICT,
   CONSTRAINT chk_servicopecas_total CHECK (preco_total = preco_unitario * quantidade)
)

-- Reservas
CREATE TABLE reservas (
   reserva_id      SERIAL PRIMARY KEY,
   cliente_id      INT NOT NULL,
   carro_id        INT NOT NULL,
   data_reserva    DATE NOT NULL DEFAULT CURRENT_DATE,
   data_teste      DATE,
   estado          VARCHAR(20) NOT NULL DEFAULT 'pendente' CHECK (estado IN ('pendente', 'confirmada', 'cancelada', 'expirada')),
   observacoes     TEXT,
   criado_por_id   INT,
   CONSTRAINT FK_RESERVAS_CLIENTE FOREIGN KEY (cliente_id)
      REFERENCES clientes (cliente_id) ON DELETE RESTRICT,
   CONSTRAINT FK_RESERVAS_CARRO FOREIGN KEY (carro_id)
      REFERENCES carros (carro_id) ON DELETE RESTRICT,
   CONSTRAINT FK_RESERVAS_CRIADO_POR FOREIGN KEY (criado_por_id)
      REFERENCES utilizadores (user_id) ON DELETE SET NULL
);

-- Vendas
CREATE TABLE vendas (
   venda_id        SERIAL PRIMARY KEY,
   cliente_id      INT NOT NULL,
   carro_id        INT NOT NULL,
   funcionario_id  INT,
   data            DATE NOT NULL DEFAULT CURRENT_DATE,
   preco_final     DECIMAL(10,2) NOT NULL,
   forma_pagamento VARCHAR(50),
   observacoes     TEXT,
   CONSTRAINT FK_VENDAS_CLIENTE FOREIGN KEY (cliente_id)
      REFERENCES clientes (cliente_id) ON DELETE RESTRICT,
   CONSTRAINT FK_VENDAS_CARRO FOREIGN KEY (carro_id)
      REFERENCES carros (carro_id) ON DELETE RESTRICT,
   CONSTRAINT FK_VENDAS_FUNCIONARIO FOREIGN KEY (funcionario_id)
      REFERENCES funcionarios (funcionario_id) ON DELETE SET NULL
);

-- ============================================
-- TABELAS TRANSACIONAIS (Oficina)
-- ============================================

-- Ordens Serviço
CREATE TABLE ordens_servico (
   ordem_servico_id SERIAL PRIMARY KEY,
   cliente_id      INT NOT NULL,
   nome_veiculo    VARCHAR(200) NOT NULL, 
   tipo_servico_id INT NOT NULL,
   mecanico_id     INT,
   baia_id         INT,
   orcamento_id    INT,
   data_entrada    DATE NOT NULL DEFAULT CURRENT_DATE,
   data_prevista_saida DATE,
   data_saida      DATE,
   status          VARCHAR(20) NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'em_andamento', 'concluida', 'cancelada')),
   prioridade      VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (prioridade IN ('baixa', 'normal', 'alta', 'urgente')),
   descricao_problema TEXT,
   descricao_solucao TEXT,
   valor_total     DECIMAL(10,2),
   valor_mao_obra  DECIMAL(10,2),
   valor_pecas     DECIMAL(10,2),
   observacoes     TEXT,
   criado_por_id   INT,
   CONSTRAINT FK_ORDENSSERVICO_CLIENTE FOREIGN KEY (cliente_id)
      REFERENCES clientes (cliente_id) ON DELETE RESTRICT,
   CONSTRAINT FK_ORDENSSERVICO_TIPO_SERVICO FOREIGN KEY (tipo_servico_id)
      REFERENCES tipos_servico (tipo_servico_id) ON DELETE RESTRICT,
   CONSTRAINT FK_ORDENSSERVICO_MECANICO FOREIGN KEY (mecanico_id)
      REFERENCES mecanicos (mecanico_id) ON DELETE SET NULL,
   CONSTRAINT FK_ORDENSSERVICO_BAIA FOREIGN KEY (baia_id)
      REFERENCES baias_oficina (baia_id) ON DELETE SET NULL,
   CONSTRAINT FK_ORDENSSERVICO_CRIADO_POR FOREIGN KEY (criado_por_id)
      REFERENCES utilizadores (user_id) ON DELETE SET NULL
);

-- ============================================
-- AVALIAÇÕES
-- ============================================

CREATE TABLE avaliacoes (
   avaliacao_id    SERIAL PRIMARY KEY,
   cliente_id      INT,
   carro_id        INT,
   ordem_servico_id INT,
   tipo_avaliacao  VARCHAR(20) NOT NULL DEFAULT 'venda' CHECK (tipo_avaliacao IN ('venda', 'servico', 'geral')),
   classificacao   INT NOT NULL CHECK (classificacao BETWEEN 1 AND 5),
   comentario      TEXT,
   data_avaliacao  DATE NOT NULL DEFAULT CURRENT_DATE,
   resposta        TEXT,
   data_resposta   DATE,
   CONSTRAINT FK_AVALIACOES_CLIENTE FOREIGN KEY (cliente_id)
      REFERENCES clientes (cliente_id) ON DELETE SET NULL,
   CONSTRAINT FK_AVALIACOES_CARRO FOREIGN KEY (carro_id)
      REFERENCES carros (carro_id) ON DELETE SET NULL,
   CONSTRAINT FK_AVALIACOES_ORDEM_SERVICO FOREIGN KEY (ordem_servico_id)
      REFERENCES ordens_servico (ordem_servico_id) ON DELETE SET NULL
);

-- ============================================
-- INDEXES
-- ============================================

-- carros
CREATE INDEX idx_carros_stand ON carros(stand_id);
CREATE INDEX idx_carros_marca ON carros(marca_id);
CREATE INDEX idx_carros_estado ON carros(estado);
CREATE INDEX idx_carros_status ON carros(status_disponibilidade);
CREATE INDEX idx_carros_data_aquisicao ON carros(data_aquisicao);

-- funcionarios
CREATE INDEX idx_funcionarios_stand ON funcionarios(stand_id);

-- gerentes
CREATE INDEX idx_gerentes_stand ON gerentes(stand_id);
CREATE INDEX idx_gerentes_email ON gerentes(email);

-- mecanicos
CREATE INDEX idx_mecanicos_stand ON mecanicos(stand_id);

-- admins
CREATE INDEX idx_admins_email ON admins(email);
CREATE INDEX idx_admins_ativo ON admins(ativo);

-- utilizadores
CREATE INDEX idx_utilizadores_email ON utilizadores(email);
CREATE INDEX idx_utilizadores_role ON utilizadores(role);
CREATE INDEX idx_utilizadores_ativo ON utilizadores(ativo);
CREATE INDEX idx_utilizadores_admin_id ON utilizadores(admin_id);
CREATE INDEX idx_utilizadores_gerente_id ON utilizadores(gerente_id);
CREATE INDEX idx_utilizadores_cliente_id ON utilizadores(cliente_id);
CREATE INDEX idx_utilizadores_funcionario_id ON utilizadores(funcionario_id);
CREATE INDEX idx_utilizadores_mecanico_id ON utilizadores(mecanico_id);

-- reservas
CREATE INDEX idx_reservas_estado ON reservas(estado);
CREATE INDEX idx_reservas_cliente ON reservas(cliente_id);
CREATE INDEX idx_reservas_carro ON reservas(carro_id);

-- vendas
CREATE INDEX idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX idx_vendas_data ON vendas(data);
CREATE INDEX idx_vendas_funcionario ON vendas(funcionario_id);
CREATE INDEX idx_vendas_carro ON vendas(carro_id);

-- ordens_servico
CREATE INDEX idx_ordens_status ON ordens_servico(status);
CREATE INDEX idx_ordens_cliente ON ordens_servico(cliente_id);
CREATE INDEX idx_ordens_mecanico ON ordens_servico(mecanico_id);
CREATE INDEX idx_ordens_tipo_servico ON ordens_servico(tipo_servico_id);
CREATE INDEX idx_ordens_baia ON ordens_servico(baia_id);
CREATE INDEX idx_ordens_prioridade ON ordens_servico(prioridade);
CREATE INDEX idx_ordens_data_entrada ON ordens_servico(data_entrada);

-- avaliacoes
CREATE INDEX idx_avaliacoes_tipo ON avaliacoes(tipo_avaliacao);
CREATE INDEX idx_avaliacoes_classificacao ON avaliacoes(classificacao);

-- pecas_acessorios
CREATE INDEX idx_pecas_stock ON pecas_acessorios(stock_atual);

-- baias_oficina
CREATE INDEX idx_baias_status ON baias_oficina(status);