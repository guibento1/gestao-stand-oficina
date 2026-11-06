from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Stand(models.Model):
    stand_id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    localizacao = models.CharField(max_length=150)
    contacto = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    capacidade_oficina = models.IntegerField(default=0)

    class Meta:
        db_table = 'stands'
        verbose_name = 'Stand'
        verbose_name_plural = 'Stands'

    def __str__(self):
        return self.nome


class Marca(models.Model):
    marca_id = models.AutoField(primary_key=True)
    país_origem = models.CharField(max_length=50)
    m_nome = models.CharField(max_length=100, verbose_name='Nome')

    class Meta:
        db_table = 'marcas'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.m_nome


class Fornecedor(models.Model):
    TIPO_CHOICES = [
        ('carros', 'Carros'),
        ('pecas', 'Peças'),
        ('ambos', 'Ambos'),
    ]

    fornecedor_id = models.AutoField(primary_key=True)
    f_nome = models.CharField(max_length=150, verbose_name='Nome')
    f_contacto = models.CharField(max_length=50, verbose_name='Contacto')
    f_email = models.EmailField(unique=True, verbose_name='Email')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)

    class Meta:
        db_table = 'fornecedores'
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.f_nome


class PecaAcessorio(models.Model):
    peca_id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    codigo_fabricante = models.CharField(max_length=50, blank=True, null=True)
    preço = models.DecimalField(max_digits=10, decimal_places=2)
    stock_atual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)

    class Meta:
        db_table = 'pecas_acessorios'
        verbose_name = 'Peça/Acessório'
        verbose_name_plural = 'Peças/Acessórios'

    def __str__(self):
        return self.nome


class TipoServico(models.Model):
    tipo_servico_id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    tempo_estimado = models.IntegerField(help_text='Tempo estimado em minutos')
    preco_base = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'tipos_servico'
        verbose_name = 'Tipo de Serviço'
        verbose_name_plural = 'Tipos de Serviço'

    def __str__(self):
        return self.nome


class Carro(models.Model):
    ESTADO_CHOICES = [
        ('novo', 'Novo'),
        ('usado', 'Usado'),
        ('seminovo', 'Seminovo'),
    ]

    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
        ('em_manutencao', 'Em Manutenção'),
    ]

    COMBUSTIVEL_CHOICES = [
        ('gasolina', 'Gasolina'),
        ('diesel', 'Diesel'),
        ('eletrico', 'Elétrico'),
        ('hibrido', 'Híbrido'),
        ('gpl', 'GPL'),
    ]

    carro_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    marca = models.ForeignKey(Marca, on_delete=models.RESTRICT)
    modelo = models.CharField(max_length=100)
    ano = models.IntegerField()
    preço = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    quilometragem = models.IntegerField(default=0)
    cor = models.CharField(max_length=50, blank=True, null=True)
    chassi = models.CharField(max_length=50, unique=True, blank=True, null=True)
    placa = models.CharField(max_length=20, unique=True, blank=True, null=True)
    status_disponibilidade = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    data_aquisicao = models.DateField(blank=True, null=True)
    combustivel = models.CharField(max_length=20, choices=COMBUSTIVEL_CHOICES, blank=True, null=True)
    potencia = models.IntegerField(blank=True, null=True, help_text='Potência em CV')
    cilindrada = models.IntegerField(blank=True, null=True, help_text='Cilindrada em cc')
    portas = models.IntegerField(blank=True, null=True)
    lugares = models.IntegerField(blank=True, null=True)
    ref_imagem_capa = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'carros'
        verbose_name = 'Carro'
        verbose_name_plural = 'Carros'

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.ano}"


class ImagemCarro(models.Model):
    imagem_id = models.AutoField(primary_key=True)
    carro = models.ForeignKey(Carro, on_delete=models.CASCADE, related_name='imagens')
    blob_name = models.CharField(max_length=255)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ordem = models.IntegerField(default=0)
    is_capa = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey('Utilizador', on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'imagens_carros'
        verbose_name = 'Imagem do Carro'
        verbose_name_plural = 'Imagens dos Carros'
        ordering = ['ordem']

    def __str__(self):
        return f"Imagem de {self.carro} - {self.blob_name}"


class BaiaOficina(models.Model):
    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('ocupada', 'Ocupada'),
        ('manutencao', 'Manutenção'),
    ]

    baia_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    numero_baia = models.CharField(max_length=10)
    tipo = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='disponivel')

    class Meta:
        db_table = 'baias_oficina'
        verbose_name = 'Baia da Oficina'
        verbose_name_plural = 'Baias da Oficina'
        unique_together = [['stand', 'numero_baia']]

    def __str__(self):
        return f"Baia {self.numero_baia} - {self.stand}"


class Equipamento(models.Model):
    STATUS_CHOICES = [
        ('operacional', 'Operacional'),
        ('manutencao', 'Manutenção'),
        ('inativo', 'Inativo'),
    ]

    equipamento_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    fabricante = models.CharField(max_length=100, blank=True, null=True)
    data_aquisicao = models.DateField()
    valor_aquisicao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    proxima_manutencao = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='operacional')

    class Meta:
        db_table = 'equipamentos'
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'

    def __str__(self):
        return self.nome


class HorarioFuncionamento(models.Model):
    horario_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    dia_semana = models.IntegerField(choices=[
        (0, 'Domingo'), (1, 'Segunda'), (2, 'Terça'), (3, 'Quarta'),
        (4, 'Quinta'), (5, 'Sexta'), (6, 'Sábado')
    ])
    hora_abertura = models.TimeField()
    hora_fechamento = models.TimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'horarios_funcionamento'
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'
        unique_together = [['stand', 'dia_semana']]

    def __str__(self):
        return f"{self.stand} - Dia {self.dia_semana}"


class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    departamento = models.CharField(max_length=50, blank=True, null=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'admins'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return self.nome


class Gerente(models.Model):
    gerente_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    data_admissao = models.DateField(default=timezone.now)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'gerentes'
        verbose_name = 'Gerente'
        verbose_name_plural = 'Gerentes'

    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    funcionario_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    cargo = models.CharField(max_length=50)
    f_nome = models.CharField(max_length=100, verbose_name='Nome')
    f_email = models.EmailField(unique=True, verbose_name='Email')
    f_telefone = models.CharField(max_length=20, verbose_name='Telefone')
    data_admissao = models.DateField(default=timezone.now)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    data_saida = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'funcionarios'
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return self.f_nome


class Mecanico(models.Model):
    mecanico_id = models.AutoField(primary_key=True)
    stand = models.ForeignKey(Stand, on_delete=models.RESTRICT)
    nome = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    data_admissao = models.DateField(default=timezone.now)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'mecanicos'
        verbose_name = 'Mecânico'
        verbose_name_plural = 'Mecânicos'

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    cliente_id = models.AutoField(primary_key=True)
    c_nome = models.CharField(max_length=100, verbose_name='Nome')
    c_email = models.EmailField(unique=True, verbose_name='Email')
    c_telefone = models.CharField(max_length=20, verbose_name='Telefone')
    nif = models.CharField(max_length=20, unique=True)
    data_cadastro = models.DateField(default=timezone.now)
    data_nascimento = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.c_nome


class EnderecoCliente(models.Model):
    endereco_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, related_name='enderecos')
    rua = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)
    pais = models.CharField(max_length=100)

    class Meta:
        db_table = 'enderecos_clientes'
        verbose_name = 'Endereço do Cliente'
        verbose_name_plural = 'Endereços dos Clientes'

    def __str__(self):
        return f"{self.rua}, {self.cidade}"


class Utilizador(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('gerente', 'Gerente'),
        ('funcionario', 'Funcionário'),
        ('mecanico', 'Mecânico'),
        ('cliente', 'Cliente'),
    ]

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Foreign keys para diferentes tipos de usuários
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, blank=True, null=True)
    gerente = models.ForeignKey(Gerente, on_delete=models.SET_NULL, blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, blank=True, null=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, blank=True, null=True)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.SET_NULL, blank=True, null=True)

    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'utilizadores'
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'

    def __str__(self):
        return f"{self.email} ({self.role})"


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
    ]

    reserva_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    carro = models.ForeignKey(Carro, on_delete=models.RESTRICT)
    data_reserva = models.DateField(default=timezone.now)
    data_teste = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva de {self.cliente} para {self.carro}"


class Venda(models.Model):
    venda_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    carro = models.ForeignKey(Carro, on_delete=models.RESTRICT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, blank=True, null=True)
    data = models.DateField(default=timezone.now)
    preco_final = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=50, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'vendas'
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    def __str__(self):
        return f"Venda de {self.carro} para {self.cliente}"


class Pagamento(models.Model):
    METODO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('transferencia', 'Transferência Bancária'),
        ('cheque', 'Cheque'),
    ]

    pagamento_id = models.AutoField(primary_key=True)
    venda = models.ForeignKey(Venda, on_delete=models.RESTRICT)
    data_pagamento = models.DateField(default=timezone.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=50, choices=METODO_CHOICES)
    referencia = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'pagamentos'
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

    def __str__(self):
        return f"Pagamento de {self.valor}€ para venda {self.venda}"


class Garantia(models.Model):
    garantia_id = models.AutoField(primary_key=True)
    venda = models.ForeignKey(Venda, on_delete=models.RESTRICT)
    tipo = models.CharField(max_length=50)
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField()
    termos = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'garantias'
        verbose_name = 'Garantia'
        verbose_name_plural = 'Garantias'

    def __str__(self):
        return f"Garantia para venda {self.venda}"


class Orcamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('expirado', 'Expirado'),
    ]

    orcamento_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    carro = models.ForeignKey(Carro, on_delete=models.RESTRICT)
    tipo_servico = models.ForeignKey(TipoServico, on_delete=models.RESTRICT)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.SET_NULL, blank=True, null=True)
    data_orcamento = models.DateField(default=timezone.now)
    validade = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    descricao = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'orcamentos'
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'

    def __str__(self):
        return f"Orçamento para {self.carro} - {self.tipo_servico}"


class OrcamentoItem(models.Model):
    orcamento_item_id = models.AutoField(primary_key=True)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens')
    peca = models.ForeignKey(PecaAcessorio, on_delete=models.SET_NULL, blank=True, null=True)
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'orcamento_itens'
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens dos Orçamentos'

    def __str__(self):
        return f"{self.descricao} - {self.quantidade}x{self.valor_unitario}€"


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    ordem_servico_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    nome_veiculo = models.CharField(max_length=200, verbose_name='Nome do Veículo')  # Substituindo FK carro
    tipo_servico = models.ForeignKey(TipoServico, on_delete=models.RESTRICT)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.SET_NULL, blank=True, null=True)
    baia = models.ForeignKey(BaiaOficina, on_delete=models.SET_NULL, blank=True, null=True)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, blank=True, null=True)
    data_entrada = models.DateField(default=timezone.now)
    data_prevista_saida = models.DateField(blank=True, null=True)
    data_saida = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='normal')
    descricao_problema = models.TextField(blank=True, null=True)
    descricao_solucao = models.TextField(blank=True, null=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'ordens_servico'
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'

    def __str__(self):
        return f"OS {self.ordem_servico_id} - {self.nome_veiculo}"


class ServicoPeca(models.Model):
    servico_peca_id = models.AutoField(primary_key=True)
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='pecas')
    peca = models.ForeignKey(PecaAcessorio, on_delete=models.RESTRICT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'servico_pecas'
        verbose_name = 'Peça do Serviço'
        verbose_name_plural = 'Peças dos Serviços'

    def __str__(self):
        return f"{self.peca} - {self.quantidade}x{self.preco_unitario}€"


class Compra(models.Model):
    compra_id = models.AutoField(primary_key=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.RESTRICT)
    carro = models.OneToOneField(Carro, on_delete=models.RESTRICT)
    data_compra = models.DateField(default=timezone.now)
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'compras'
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'

    def __str__(self):
        return f"Compra de {self.carro}"


class CompraPeca(models.Model):
    compra_peca_id = models.AutoField(primary_key=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.RESTRICT)
    peca = models.ForeignKey(PecaAcessorio, on_delete=models.RESTRICT)
    data_compra = models.DateField(default=timezone.now)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'compras_pecas'
        verbose_name = 'Compra de Peça'
        verbose_name_plural = 'Compras de Peças'

    def __str__(self):
        return f"Compra de {self.peca}"


class FornecedorPeca(models.Model):
    fornecedor_peca_id = models.AutoField(primary_key=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE)
    peca = models.ForeignKey(PecaAcessorio, on_delete=models.CASCADE)
    preco_fornecedor = models.DecimalField(max_digits=10, decimal_places=2)
    prazo_entrega = models.IntegerField(default=0, help_text='Prazo em dias')

    class Meta:
        db_table = 'fornecedores_pecas'
        verbose_name = 'Fornecedor de Peça'
        verbose_name_plural = 'Fornecedores de Peças'
        unique_together = [['fornecedor', 'peca']]

    def __str__(self):
        return f"{self.fornecedor} - {self.peca}"


class Avaliacao(models.Model):
    TIPO_CHOICES = [
        ('venda', 'Venda'),
        ('servico', 'Serviço'),
        ('geral', 'Geral'),
    ]

    avaliacao_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, blank=True, null=True)
    carro = models.ForeignKey(Carro, on_delete=models.SET_NULL, blank=True, null=True)
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.SET_NULL, blank=True, null=True)
    tipo_avaliacao = models.CharField(max_length=20, choices=TIPO_CHOICES, default='venda')
    classificacao = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(blank=True, null=True)
    data_avaliacao = models.DateField(default=timezone.now)
    resposta = models.TextField(blank=True, null=True)
    data_resposta = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'avaliacoes'
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return f"Avaliação {self.avaliacao_id} - {self.classificacao} estrelas"
