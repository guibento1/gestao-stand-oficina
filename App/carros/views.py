from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import connection, transaction
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import json
import logging
import os
from django.conf import settings
from azure.utils import update_file, generate_sas_url

try:
    from azure.utils import delete_file
except ImportError:
    delete_file = None
import asyncio
from .models import Mecanico, Carro, Cliente, TipoServico, OrdemServico, BaiaOficina, Utilizador
from .models import Mecanico, Carro, Cliente, TipoServico, OrdemServico, BaiaOficina, Utilizador, Venda

logger = logging.getLogger(__name__)

# =============================
# Funções de autenticação e permissões
# =============================

def is_staff_user(user):
    # Verifica se o utilizador é staff
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def eliminar_imagem_carro_view(request, imagem_id):
    # Elimina uma imagem de carro (apenas staff)
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT blob_name, carro_id, is_capa FROM imagens_carros WHERE imagem_id = %s", [imagem_id])
                row = cursor.fetchone()
                if not row:
                    messages.error(request, 'Imagem não encontrada.')
                    return redirect('carros')
                blob_name, carro_id, is_capa = row
                # Remover ficheiro do Azure (para novos registros com nome do blob ou URLs antigas)
                if not blob_name.startswith('/media/'):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        if delete_file:
                            loop.run_until_complete(delete_file(blob_name, 'carros'))
                    except Exception as e:
                        print(f"Erro ao deletar do Azure: {e}")
                # Remover ficheiro do disco se for local
                else:
                    caminho = os.path.join(settings.BASE_DIR, blob_name.lstrip('/'))
                    if os.path.exists(caminho):
                        os.remove(caminho)
                cursor.execute("CALL sp_eliminar_imagem_carro(%s)", [imagem_id])
                # Se era imagem de capa, limpar ref_imagem_capa
                if is_capa:
                    cursor.execute("CALL sp_limpar_ref_imagem_capa(%s)", [carro_id])
            messages.success(request, 'Imagem eliminada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar imagem: {str(e)}')
    return redirect('carros')


@login_required
@user_passes_test(is_staff_user)
def upload_imagem_carro_view(request, carro_id):
    # Faz upload de imagem de carro para Azure (apenas staff)
    if request.method == 'POST' and request.FILES.get('imagem'):
        imagem = request.FILES['imagem']
        descricao = request.POST.get('descricao') or ''
        is_capa = bool(request.POST.get('is_capa'))
        user_id = request.user.id
        container = 'carros'  # nome do container no Azure
        try:
            # Upload para Azure Blob Storage (async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            blob_url = loop.run_until_complete(update_file(imagem, container))
            
            # Extrair apenas o nome do blob da URL
            # Formato da URL: https://account.blob.core.windows.net/container/blobname
            blob_name = blob_url.split('/')[-1] if '/' in blob_url else blob_url
            
            # Guardar apenas o nome do blob no BD
            with connection.cursor() as cursor:
                # Delegar inserção da imagem e atualizações relacionadas para uma procedure
                cursor.execute("CALL sp_inserir_imagem_carro(%s, %s, %s, %s, %s, %s)",
                               [carro_id, blob_name, descricao, 0, is_capa, user_id])
            messages.success(request, 'Imagem carregada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao guardar imagem: {str(e)}')
    else:
        messages.error(request, 'Selecione uma imagem para upload.')
    return redirect('carros')

# Upload local duplicado removido; usar o handler baseado em Azure definido acima.


def is_staff_user(user):
    """Verifica se o utilizador é staff"""
    return user.is_staff


def is_superuser(user):
    # Verifica se é superuser/admin
    return user.is_superuser


def get_user_role_by_email(email):
    # Obtém o role do utilizador pelo email
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT role FROM utilizadores WHERE email = %s", [email])
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return None


def get_user_role(request):
    # Obtém o role do utilizador (sessão ou BD)
    # Tentar obter da sessão primeiro (mais rápido)
    if 'user_role' in request.session:
        return request.session['user_role']
    
    # Se não estiver na sessão, buscar da BD
    if request.user.is_authenticated:
        role = get_user_role_by_email(request.user.email)
        return role
    return None


def is_gerente_or_above(request):
    # Verifica se é gerente ou admin (request)
    role = get_user_role(request)
    return role in ['admin', 'gerente']


def can_access_oficina_user(user):
    # Verifica se pode aceder à oficina
    if user.is_superuser:
        return True
    role = get_user_role_by_email(user.email)
    return role in ['admin', 'gerente', 'funcionario', 'mecanico', 'cliente']


def is_funcionario_or_above(request):
    # Verifica se é funcionário, gerente ou admin (request)
    role = get_user_role(request)
    return role in ['admin', 'gerente', 'funcionario']


# =============================
# Funções auxiliares para listas e dados
# =============================

def get_marcas():
    # Devolve lista de marcas para dropdowns
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT marca_id, m_nome FROM marcas ORDER BY m_nome")
            rows = cursor.fetchall()
            # Retorna múltiplos nomes de chave para compatibilidade com templates que usem diferentes estilos
            return [
                {
                    'id': row[0], 'nome': row[1],
                    'marca_id': row[0], 'm_nome': row[1]
                }
                for row in rows
            ]
    except Exception:
        return []


def get_stands():
    # Devolve lista de stands para dropdowns
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT stand_id, localizacao FROM stands ORDER BY localizacao")
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0], 'localizacao': row[1],
                    'stand_id': row[0]
                }
                for row in rows
            ]
    except Exception:
        return []


def get_clientes_list():
    # Devolve lista de clientes para dropdowns
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cliente_id, c_nome FROM clientes ORDER BY c_nome")
            return [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]
    except Exception:
        return []


def get_carros_list():
    # Devolve lista de todos os carros para dropdowns
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT carro_id, marca || ' - ' || modelo || ' (' || ano || ') - ' || status_disponibilidade AS info FROM vw_carros_completos ORDER BY marca, modelo")
            return [{'id': row[0], 'info': row[1]} for row in cursor.fetchall()]
    except Exception:
        return []


def get_carros_disponiveis():
    # Devolve lista de carros disponíveis para dropdowns
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT v.carro_id, m.m_nome || ' - ' || v.modelo || ' (' || v.ano || ')' AS info FROM vw_carros_disponiveis v JOIN marcas m ON v.marca_id = m.marca_id ORDER BY m.m_nome, v.modelo")
            return [{'id': row[0], 'info': row[1]} for row in cursor.fetchall()]
    except Exception:
        return []



# =============================
# Páginas públicas
# =============================

def home_view(request):
    # Página inicial com estatísticas
    stats = {'carros': 0, 'clientes': 0, 'vendas': 0, 'avaliacoes': 0}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM carros")
            stats['carros'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes")
            stats['clientes'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendas")
            stats['vendas'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM avaliacoes")
            stats['avaliacoes'] = cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
    
    return render(request, 'home.html', {'stats': stats})


def autenticar_utilizador_postgres(email, password):
    # Autentica utilizador contra a tabela 'utilizadores' do PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM fn_autenticar_utilizador(%s, %s)", [email, password])
            row = cursor.fetchone()
            if row:
                # Atualizar last_login
                cursor.execute("CALL sp_atualizar_last_login(%s)", [row[0]])
                return {
                    'user_id': row[0],
                    'email': row[1],
                    'role': row[2],
                    'ativo': row[3],
                    'nome': row[4]
                }
    except Exception as e:
        logger.error(f"Erro na autenticação PostgreSQL: {e}")
        # Fazer rollback para limpar a transação abortada
        try:
            connection.rollback()
        except:
            pass
    return None


def login_view(request):
    # Página de login (autentica contra tabela utilizadores do PostgreSQL)
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Primeiro tenta autenticar via PostgreSQL (tabela utilizadores)
        pg_user = autenticar_utilizador_postgres(username, password)
        
        if pg_user:
            # Criar ou atualizar utilizador Django baseado nos dados do PostgreSQL
            from django.contrib.auth.models import User
            
            user, created = User.objects.get_or_create(
                username=pg_user['email'],
                defaults={
                    'email': pg_user['email'],
                    'first_name': pg_user['nome'].split()[0] if pg_user['nome'] else '',
                    'last_name': ' '.join(pg_user['nome'].split()[1:]) if pg_user['nome'] and len(pg_user['nome'].split()) > 1 else '',
                }
            )
            
            # Atualizar permissões baseado no role
            if pg_user['role'] == 'admin':
                user.is_superuser = True
                user.is_staff = True
            elif pg_user['role'] in ['gerente', 'funcionario', 'mecanico']:
                user.is_superuser = False
                user.is_staff = True
            else:  # cliente
                user.is_superuser = False
                user.is_staff = False
            
            user.save()
            
            # Fazer login no Django
            login(request, user)
            
            # Guardar a role na sessão para uso nas views
            request.session['user_role'] = pg_user['role']
            request.session['user_id'] = pg_user['user_id']
            
            messages.success(request, f'Bem-vindo, {pg_user["nome"]}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        
        # Fallback: tentar autenticação Django padrão
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        
        return render(request, 'login.html', {'error': 'Email ou password inválidos'})
    
    return render(request, 'login.html')


def logout_view(request):
    # Logout do utilizador
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Sessão terminada com sucesso.')
        return redirect('home')
    return render(request, 'logout.html')


def avaliacoes_view(request):
    # Lista e adiciona avaliações (público)
    avaliacoes = []
    cliente_logado = None
    
    # Obter cliente_id do utilizador logado
    if request.user.is_authenticated:
        try:
            with connection.cursor() as cursor:
                # Se for staff, pode escolher cliente; se for cliente, usa o seu próprio id
                if not request.user.is_staff:
                    # Pedir colunas explícitas para garantir ordem correta
                    cursor.execute("SELECT cliente_id, c_nome FROM vw_clientes_utilizadores WHERE email = %s", [request.user.email])
                    row = cursor.fetchone()
                    if row:
                        cliente_logado = {'id': row[0], 'nome': row[1]}
        except Exception as e:
            logger.error(f"Erro ao obter cliente logado: {e}")
    
    # POST - Adicionar avaliação (requer autenticação)
    if request.method == 'POST' and request.user.is_authenticated:
        # Se for cliente, usa o seu próprio id; se for staff, pode escolher
        if cliente_logado:
            cliente_id = cliente_logado['id']
        else:
            cliente_id = request.POST.get('cliente_id')
        
        carro_id = request.POST.get('carro_id')
        tipo_avaliacao = 'venda'  # Sempre venda
        classificacao = request.POST.get('classificacao')
        comentario = request.POST.get('comentario') or None
        
        if not cliente_id or not carro_id:
            messages.error(request, 'Cliente e carro são obrigatórios.')
        else:
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # sp_inserir_avaliacao(p_cliente_id, p_tipo_avaliacao, p_classificacao, p_carro_id, p_ordem_servico_id, p_comentario)
                        cursor.execute("CALL sp_inserir_avaliacao(%s, %s, %s, %s, %s, %s)",
                                      [cliente_id, tipo_avaliacao, classificacao, carro_id, None, comentario])
                messages.success(request, 'Avaliação adicionada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao adicionar avaliação: {str(e)}')
    
    # GET - Listar avaliações
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_avaliacoes_detalhes")
            columns = [col[0] for col in cursor.description]
            avaliacoes = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao listar avaliações: {e}")
    
    # Buscar ordens de serviço concluídas para avaliações de serviço
    ordens_servico_cliente = []
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    os.ordem_servico_id,
                    ts.nome AS tipo_servico,
                    os.nome_veiculo AS carro_info,
                    os.data_entrada,
                    os.status
                FROM ordens_servico os
                JOIN tipos_servico ts ON os.tipo_servico_id = ts.tipo_servico_id
                WHERE os.status = 'concluido'
            """
            params = []
            if cliente_logado:
                query += " AND os.cliente_id = %s"
                params.append(cliente_logado['id'])
            query += " ORDER BY os.data_entrada DESC"
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            ordens_servico_cliente = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao buscar ordens de serviço: {e}")
    
    # Determinar role do utilizador e se é cliente
    user_role = get_user_role(request)
    eh_cliente = user_role == 'cliente'

    # Se for cliente, determinar cliente_id para auto-preenchimento nos eventos
    evento_cliente_id = None
    if eh_cliente:
        try:
            cliente_obj_for_event = Cliente.objects.get(c_email=request.user.email)
            evento_cliente_id = cliente_obj_for_event.cliente_id
        except Cliente.DoesNotExist:
            evento_cliente_id = None

    context = {
        'avaliacoes': avaliacoes,
        'clientes': get_clientes_list(),
        'carros': get_carros_list(),
        'cliente_logado': cliente_logado,
        'ordens_servico_cliente': ordens_servico_cliente,
        'evento_cliente_id': evento_cliente_id,
        'pode_eliminar_todas': is_funcionario_or_above(request),
    }
    return render(request, 'avaliacoes.html', context)


@login_required
def eliminar_avaliacao_view(request, avaliacao_id):
    """Eliminar avaliação - funcionário/gerente/admin pode eliminar qualquer, mecânico/cliente só as suas"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                # Verificar se o utilizador pode eliminar qualquer avaliação
                if is_funcionario_or_above(request):
                    # Funcionário, gerente ou admin pode eliminar qualquer avaliação
                    cursor.execute("CALL sp_eliminar_avaliacao(%s)", [avaliacao_id])
                else:
                    # Mecânico e cliente só podem eliminar as suas próprias avaliações
                    # Primeiro, tentar encontrar o cliente_id associado ao utilizador
                    try:
                        cursor.execute("CALL sp_eliminar_avaliacao_por_utilizador(%s, %s)", [avaliacao_id, request.user.email])
                    except Exception as e:
                        messages.error(request, 'Não tem permissão para eliminar esta avaliação.')
                        return redirect('avaliacoes')
                
            messages.success(request, 'Avaliação eliminada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar avaliação: {str(e)}')
    return redirect('avaliacoes')


# =============================
# Secção de carros
# =============================

@login_required
def carros_view(request):
    # Lista e adiciona carros
    carros = []
    pode_gerir = is_funcionario_or_above(request)

    # POST - Adicionar carro (apenas funcionário ou acima, não mecânico)
    if request.method == 'POST' and pode_gerir:
        standid = request.POST.get('standid')
        marcaid = request.POST.get('marcaid')
        modelo = request.POST.get('modelo')
        ano = request.POST.get('ano')
        preco = request.POST.get('preco')
        estado = request.POST.get('estado', 'novo')
        imagem_capa = request.FILES.get('imagem_capa')
        # TODO: adicionar campos extra se necessário
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_inserir_carro(%s, %s, %s, %s, %s, %s)",
                                  [standid, marcaid, modelo, ano, preco, estado])
                    # Obter o ID do carro recém-criado
                    cursor.execute("SELECT currval('carros_carro_id_seq')")
                    carro_id = cursor.fetchone()[0]
                    
                    # Se foi enviada uma imagem de capa, fazer upload
                    if imagem_capa:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        blob_url = loop.run_until_complete(update_file(imagem_capa, 'carros'))
                        
                        # Extrair apenas o nome do blob da URL
                        blob_name = blob_url.split('/')[-1] if '/' in blob_url else blob_url
                        
                        # Inserir imagem como capa
                        cursor.execute("CALL sp_inserir_imagem_carro(%s, %s, %s, %s, %s, %s)",
                                       [carro_id, blob_name, 'Imagem de capa', 0, True, request.user.id])
            messages.success(request, 'Carro adicionado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar carro: {str(e)}')

    # GET - Listar carros e imagens
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_carros_completos")
            columns = [col[0] for col in cursor.description]
            carros_raw = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Buscar imagens para cada carro
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM imagens_carros ORDER BY carro_id, is_capa DESC, ordem ASC, imagem_id ASC")
            imagens_raw = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

        imagens_by_carro = {}
        for img in imagens_raw:
            imagens_by_carro.setdefault(img['carro_id'], []).append(img)

        # Juntar imagens, gerar SAS temporário e preparar lista final
        for carro in carros_raw:
            carro['imagens'] = imagens_by_carro.get(carro['carro_id'], [])
            # gerar SAS/URL para cada imagem
            for img in carro['imagens']:
                blob = img.get('blob_name')
                if not blob:
                    img['sas_url'] = None
                else:
                    # Sempre gerar uma nova SAS URL, extraindo o nome do blob se necessário
                    try:
                        if isinstance(blob, str) and blob.startswith('https://') and '.blob.core.windows.net' in blob:
                            # Extrair nome do blob da URL antiga
                            # Formato da URL: https://account.blob.core.windows.net/container/blobname
                            parts = blob.split('/')
                            if len(parts) >= 5:
                                blob_name = parts[4]  # blobname após container
                            else:
                                blob_name = blob
                        else:
                            blob_name = blob
                        
                        img['sas_url'] = generate_sas_url(blob_name, 'carros')
                    except Exception as e:
                        logger.error(f"Erro ao gerar SAS URL para {blob}: {e}")
                        img['sas_url'] = None
            # Definir imagem de capa (ref_imagem_capa ou primeira imagem marcada como capa)
            capa = next((img for img in carro['imagens'] if img.get('is_capa')), None)
            if not capa and carro['imagens']:
                capa = carro['imagens'][0]
            carro['imagem_capa'] = capa.get('sas_url') if capa else None
            carros.append(carro)
    except Exception as e:
        logger.error(f"Erro ao listar carros: {e}")

    context = {
        'carros': carros,
        'marcas': get_marcas(),
        'stands': get_stands(),
        'pode_gerir': pode_gerir,
    }
    return render(request, 'carros.html', context)


def check_gerente_or_above(user):
    # Decorator: gerente ou admin
    return get_user_role_by_email(user.email) in ['admin', 'gerente']

def check_funcionario_or_above(user):
    # Decorator: funcionário, gerente ou admin
    return get_user_role_by_email(user.email) in ['admin', 'gerente', 'funcionario']


from django.http import HttpResponseForbidden
from functools import wraps

def check_can_access_oficina(view_func):
    # Decorator: permite acesso à oficina apenas a admin, gerente ou mecânico
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not can_access_oficina_user(request.user):
            return HttpResponseForbidden("Acesso à oficina não permitido.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@user_passes_test(check_gerente_or_above)
def editar_carro_view(request, carro_id):
    carro = None
    imagens = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM carros WHERE carro_id = %s", [carro_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                carro = dict(zip(columns, row))
        if carro:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM imagens_carros WHERE carro_id = %s ORDER BY is_capa DESC, ordem ASC, imagem_id ASC", [carro_id])
                imagens = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            # Gerar SAS temporário para cada imagem (ou usar URL/local se já for completo)
            for img in imagens:
                blob = img.get('blob_name')
                if not blob:
                    img['sas_url'] = None
                elif isinstance(blob, str) and blob.startswith('/media/'):
                    img['sas_url'] = blob
                elif isinstance(blob, str) and blob.startswith('https://') and '.blob.core.windows.net' in blob:
                    # É uma URL do Azure, gerar SAS
                    try:
                        img['sas_url'] = generate_sas_url(blob, 'carros')
                    except Exception:
                        img['sas_url'] = blob
                else:
                    # Assume que é um nome de blob antigo, gerar SAS
                    try:
                        img['sas_url'] = generate_sas_url(blob, 'carros')
                    except Exception:
                        img['sas_url'] = blob
    except Exception as e:
        messages.error(request, f'Erro ao obter carro: {str(e)}')
        return redirect('carros')
    if not carro:
        messages.error(request, 'Carro não encontrado.')
        return redirect('carros')

    if request.method == 'POST':
        # Atualizar todos os campos do carro
        campos = [
            'stand_id', 'marca_id', 'modelo', 'ano', 'preço', 'estado', 'quilometragem', 'cor', 'chassi', 'placa',
            'status_disponibilidade', 'data_aquisicao', 'combustivel', 'potencia', 'cilindrada', 'portas', 'lugares'
        ]
        # Ler valores do form para cada campo
        dados = {c: request.POST.get(c) for c in campos}
        # Compatibilidade: aceitar também 'preco' sem acento vindo do formulário
        if 'preço' in dados and not dados['preço']:
            dados['preço'] = request.POST.get('preco') or None

        # Campos inteiros que podem vir vazios -> converter '' para None ou int
        int_fields = {'stand_id', 'marca_id', 'ano', 'quilometragem', 'potencia', 'cilindrada', 'portas', 'lugares'}
        for f in int_fields:
            v = dados.get(f)
            if v is None or v == '':
                dados[f] = None
            else:
                try:
                    dados[f] = int(v)
                except Exception:
                    dados[f] = None

        # Data: aceitar vazio como NULL
        if dados.get('data_aquisicao') in (None, ''):
            dados['data_aquisicao'] = None

        # Deixar preço como string/decimal (DB driver converte) ou None
        if dados.get('preço') in (None, ''):
            dados['preço'] = None

        valores = [dados[c] for c in campos]
        updated = False
        try:
            # Chamar procedure que centraliza validações e atualizações
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL sp_atualizar_carro(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [carro_id,
                     dados.get('stand_id'),
                     dados.get('marca_id'),
                     dados.get('modelo'),
                     dados.get('ano'),
                     dados.get('preço'),
                     dados.get('estado'),
                     dados.get('quilometragem'),
                     dados.get('cor'),
                     dados.get('chassi'),
                     dados.get('placa'),
                     dados.get('status_disponibilidade'),
                     dados.get('data_aquisicao'),
                     dados.get('combustivel'),
                     dados.get('potencia'),
                     dados.get('cilindrada'),
                     dados.get('portas'),
                     dados.get('lugares')]
                )
            updated = True
            messages.success(request, 'Carro atualizado com sucesso!')
        except Exception as e:
            try:
                connection.rollback()
            except Exception:
                pass
            messages.error(request, f'Erro ao atualizar carro: {str(e)}')

        # Atualizar imagens: descrição, ordem, capa, eliminar
        ref_imagem_capa = None
        for img in imagens:
            img_id = str(img['imagem_id'])
            desc = request.POST.get(f'descricao_{img_id}', img['descricao'])
            ordem = request.POST.get(f'ordem_{img_id}', img['ordem'])
            is_capa = request.POST.get('is_capa', '') == img_id
            if is_capa:
                ref_imagem_capa = img['blob_name']  # Agora é URL
            try:
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_atualizar_imagem_carro(%s, %s, %s, %s)", [img_id, desc, ordem, is_capa])
            except Exception as e:
                messages.warning(request, f'Erro ao atualizar imagem {img_id}: {str(e)}')

        # Atualizar ref_imagem_capa se mudou
        if ref_imagem_capa is not None:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_atualizar_ref_imagem_capa(%s, %s)", [carro_id, ref_imagem_capa])
            except Exception as e:
                messages.warning(request, f'Erro ao atualizar imagem de capa: {str(e)}')

        # Eliminar imagens marcadas
        for img in imagens:
            img_id = str(img['imagem_id'])
            if request.POST.get(f'delete_{img_id}'):
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("CALL sp_eliminar_imagem_carro(%s)", [img_id])
                except Exception as e:
                    messages.warning(request, f'Erro ao eliminar imagem {img_id}: {str(e)}')

        # Adicionar nova imagem se enviada
        nova_imagem = request.FILES.get('nova_imagem')
        if nova_imagem:
            nova_descricao = request.POST.get('nova_descricao', '')
            nova_ordem = request.POST.get('nova_ordem', 0)
            nova_is_capa = bool(request.POST.get('nova_is_capa'))
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                blob_url = loop.run_until_complete(update_file(nova_imagem, 'carros'))
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_inserir_imagem_carro(%s, %s, %s, %s, %s, %s)",
                                   [carro_id, blob_url, nova_descricao, nova_ordem, nova_is_capa, request.user.id])
                messages.success(request, 'Nova imagem adicionada com sucesso!')
                updated = True
            except Exception as e:
                messages.error(request, f'Erro ao adicionar nova imagem: {str(e)}')

        # Se atualização (ou inserção de imagem) foi bem sucedida, redirecionar para detalhes
        if updated:
            return redirect('detalhes_carro', carro_id=carro_id)

    context = {
        'carro': carro,
        'marcas': get_marcas(),
        'stands': get_stands(),
        'imagens': imagens,
    }
    return render(request, 'carros.html', context)


@login_required
@user_passes_test(check_gerente_or_above)
def eliminar_carro_view(request, carro_id):
    """Eliminar carro - apenas gerente ou admin"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_eliminar_carro(%s)", [carro_id])
            messages.success(request, 'Carro eliminado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar carro: {str(e)}')
    return redirect('carros')


# =============================
# Detalhes de carro (público)
# =============================
def detalhes_carro_view(request, carro_id):
    # Ver detalhes do carro (público)
    carro = None
    imagens = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM carros WHERE carro_id = %s", [carro_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                carro = dict(zip(columns, row))
        if carro:
            # Adicionar nomes de marca e stand
            with connection.cursor() as cursor:
                cursor.execute("SELECT m.m_nome FROM marcas m WHERE m.marca_id = %s", [carro['marca_id']])
                marca_row = cursor.fetchone()
                carro['marca'] = marca_row[0] if marca_row else 'N/A'
                
                cursor.execute("SELECT s.localizacao FROM stands s WHERE s.stand_id = %s", [carro['stand_id']])
                stand_row = cursor.fetchone()
                carro['stand'] = stand_row[0] if stand_row else 'N/A'
                
                cursor.execute("SELECT * FROM imagens_carros WHERE carro_id = %s ORDER BY is_capa DESC, ordem ASC, imagem_id ASC", [carro_id])
                imagens = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            # Gerar SAS/URL para cada imagem antes de anexar ao carro
            for img in imagens:
                blob = img.get('blob_name')
                if not blob:
                    img['sas_url'] = None
                elif isinstance(blob, str) and blob.startswith('/media/'):
                    img['sas_url'] = blob
                elif isinstance(blob, str) and blob.startswith('https://') and '.blob.core.windows.net' in blob:
                    # É uma URL do Azure, extrair nome do blob e gerar SAS
                    try:
                        # Extrair nome do blob da URL
                        if len(blob.split('/')) >= 5:
                            blob_name = blob.split('/')[-1]
                        else:
                            blob_name = blob
                        img['sas_url'] = generate_sas_url(blob_name, 'carros')
                    except Exception as e:
                        logger.error(f"Erro ao gerar SAS para URL Azure {blob}: {e}")
                        img['sas_url'] = blob
                else:
                    # Assume que é um nome de blob, gerar SAS
                    try:
                        img['sas_url'] = generate_sas_url(blob, 'carros')
                    except Exception as e:
                        logger.error(f"Erro ao gerar SAS para blob {blob}: {e}")
                        img['sas_url'] = None
            # Definir imagem de capa (se existir is_capa True, senão primeira imagem)
            capa = next((i for i in imagens if i.get('is_capa')), None)
            if not capa and imagens:
                capa = imagens[0]
            carro['imagem_capa'] = capa.get('sas_url') if capa else None
            carro['imagens'] = imagens
    except Exception as e:
        messages.error(request, f'Erro ao obter detalhes do carro: {str(e)}')
        return redirect('carros')
    if not carro:
        messages.error(request, 'Carro não encontrado.')
        return redirect('carros')
    # Permissão para editar (mostrar botão Editar na página de detalhes)
    pode_editar = is_gerente_or_above(request)
    return render(request, 'detalhes_carro.html', {'carro': carro, 'pode_editar': pode_editar})


# =============================
# Secção de clientes
# =============================

@login_required
@user_passes_test(check_funcionario_or_above)
def clientes_view(request):
    # Lista e adiciona clientes (apenas funcionário ou acima)
    clientes = []
    
    # POST - Adicionar cliente
    if request.method == 'POST':
        nome = request.POST.get('c_nome')
        email = request.POST.get('c_email')
        telefone = request.POST.get('c_telefone')
        nif = request.POST.get('nif')
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("CALL sp_inserir_cliente(%s, %s, %s, %s)",
                                  [nome, email, telefone, nif])
            messages.success(request, 'Cliente adicionado com sucesso!')
        except Exception as e:
            error_msg = str(e)
            if 'c_email' in error_msg and 'duplicate' in error_msg.lower():
                messages.error(request, f'Já existe um cliente com o email {email}')
            elif 'nif' in error_msg.lower() and 'duplicate' in error_msg.lower():
                messages.error(request, f'Já existe um cliente com o NIF {nif}')
            else:
                messages.error(request, f'Erro ao adicionar cliente: {error_msg}')
    
    # GET - Listar clientes
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_clientes_detalhes")
            columns = [col[0] for col in cursor.description]
            clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
    
    return render(request, 'clientes.html', {'clientes': clientes})


@login_required
@user_passes_test(check_gerente_or_above)
def editar_cliente_view(request, cliente_id):
    # Editar cliente (apenas gerente ou admin)
    cliente = None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM clientes WHERE cliente_id = %s", [cliente_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                cliente = dict(zip(columns, row))
    except Exception as e:
        messages.error(request, f'Erro ao obter cliente: {str(e)}')
        return redirect('clientes')
    
    if not cliente:
        messages.error(request, 'Cliente não encontrado.')
        return redirect('clientes')
    
    if request.method == 'POST':
        nome = request.POST.get('c_nome')
        email = request.POST.get('c_email')
        telefone = request.POST.get('c_telefone')
        nif = request.POST.get('nif')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_atualizar_cliente(%s, %s, %s, %s, %s, %s)",
                               [cliente_id, nome, email, telefone, nif, None])
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('clientes')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar cliente: {str(e)}')
    
    return render(request, 'editar_cliente.html', {'cliente': cliente})


@login_required
@user_passes_test(check_gerente_or_above)
def eliminar_cliente_view(request, cliente_id):
    # Eliminar cliente (apenas gerente ou admin)
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_eliminar_cliente(%s)", [cliente_id])
            messages.success(request, 'Cliente eliminado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar cliente: {str(e)}')
    return redirect('clientes')


# =============================
# Secção de vendas
# =============================

@login_required
@user_passes_test(is_staff_user)
def vendas_view(request):
    # Lista e adiciona vendas (staff pode ver, funcionário ou acima pode registar)
    vendas = []
    pode_registar = is_funcionario_or_above(request)
    
    # POST - Adicionar venda (apenas funcionário ou acima, não mecânico)
    if request.method == 'POST' and pode_registar:
        cliente_id = request.POST.get('cliente_id')
        carro_id = request.POST.get('carro_id')
        preco_final = request.POST.get('preco_final')
        forma_pagamento = request.POST.get('forma_pagamento') or None
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # sp_registar_venda(p_cliente_id, p_carro_id, p_preco_final, p_funcionario_id, p_forma_pagamento)
                    # Usa sp_registar_venda para atualizar status do carro automaticamente
                    cursor.execute("CALL sp_registar_venda(%s, %s, %s, %s, %s)",
                                  [cliente_id, carro_id, preco_final, None, forma_pagamento])
            messages.success(request, 'Venda registada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao registar venda: {str(e)}')
    
    # GET - Listar vendas
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_vendas_completas ORDER BY data DESC")
            columns = [col[0] for col in cursor.description]
            vendas = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao listar vendas: {e}")
    
    context = {
        'vendas': vendas,
        'clientes': get_clientes_list(),
        'carros': get_carros_disponiveis(),
        'pode_registar': pode_registar,
    }
    return render(request, 'vendas.html', context)


@login_required
@user_passes_test(check_funcionario_or_above)
def eliminar_venda_view(request, venda_id):
    # Eliminar venda (apenas funcionário ou acima)
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_eliminar_venda(%s)", [venda_id])
            messages.success(request, 'Venda eliminada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar venda: {str(e)}')
    return redirect('vendas')


# =============================
# Secção de reservas
# =============================

@login_required
def reservas_view(request):
    # Lista e adiciona reservas
    reservas = []
    cliente_logado = None
    
    # Obter cliente_id do utilizador logado
    try:
        with connection.cursor() as cursor:
            # Se for staff, pode escolher cliente; se for cliente, usa o seu próprio id
            if not request.user.is_staff:
                cursor.execute("""
                    SELECT c.cliente_id, c.c_nome 
                    FROM clientes c
                    JOIN utilizadores u ON u.cliente_id = c.cliente_id
                    WHERE u.email = %s
                """, [request.user.email])
                row = cursor.fetchone()
                if row:
                    cliente_logado = {'id': row[0], 'nome': row[1]}
    except Exception as e:
        logger.error(f"Erro ao obter cliente logado: {e}")
    
    # POST - Adicionar reserva
    if request.method == 'POST':
        # Se for cliente, usa o seu próprio id; se for staff, pode escolher
        if cliente_logado:
            cliente_id = cliente_logado['id']
        else:
            cliente_id = request.POST.get('cliente_id')
        
        carro_id = request.POST.get('carro_id')
        
        if not cliente_id:
            messages.error(request, 'Não foi possível identificar o cliente.')
        else:
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # sp_reservar_carro valida disponibilidade e atualiza status do carro
                        cursor.execute("CALL sp_reservar_carro(%s, %s)",
                                      [cliente_id, carro_id])
                messages.success(request, 'Reserva criada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao criar reserva: {str(e)}')
    
    # GET - Listar reservas
    try:
        with connection.cursor() as cursor:
            if cliente_logado:
                cursor.execute("SELECT * FROM vw_reservas_detalhes WHERE cliente_id = %s ORDER BY data_reserva DESC", [cliente_logado['id']])
            else:
                cursor.execute("SELECT * FROM vw_reservas_detalhes ORDER BY data_reserva DESC")
            columns = [col[0] for col in cursor.description]
            reservas = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao listar reservas: {e}")
    
    context = {
        'reservas': reservas,
        'clientes': get_clientes_list(),
        'carros': get_carros_disponiveis(),
        'cliente_logado': cliente_logado,
    }
    return render(request, 'reservas.html', context)


@login_required
@user_passes_test(is_staff_user)
def editar_reserva_view(request, reserva_id):
    # Editar estado da reserva (apenas staff)
    reserva = None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_reservas_detalhes WHERE reserva_id = %s", [reserva_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                reserva = dict(zip(columns, row))
    except Exception as e:
        messages.error(request, f'Erro ao obter reserva: {str(e)}')
        return redirect('reservas')
    
    if not reserva:
        messages.error(request, 'Reserva não encontrada.')
        return redirect('reservas')
    
    if request.method == 'POST':
        estado = request.POST.get('estado')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_atualizar_reserva(%s, %s)", [reserva_id, estado])
            messages.success(request, 'Reserva atualizada com sucesso!')
            return redirect('reservas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar reserva: {str(e)}')
    
    return render(request, 'editar_reserva.html', {'reserva': reserva})


@login_required
def eliminar_reserva_view(request, reserva_id):
    # Eliminar reserva
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_eliminar_reserva(%s)", [reserva_id])
            messages.success(request, 'Reserva eliminada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar reserva: {str(e)}')
    return redirect('reservas')


# =============================
# Secção de oficina (MongoDB)
# =============================

@login_required
@check_can_access_oficina
@login_required
def oficina_view(request):
    # Página da oficina (dados do MongoDB)
    manutencoes = []
    diagnosticos = []
    avaliacoes_detalhes = []
    eventos_integracao = []
    
    try:
        from .mongo import get_db
        db = get_db()
        
        # Obter histórico de manutenção
        manutencoes_col = db.get_collection('historico_manutencao')
        manutencoes = list(manutencoes_col.find().sort('data', -1).limit(50))
        
        # Obter diagnósticos
        diagnosticos_col = db.get_collection('diagnosticos_oficina')
        diagnosticos = list(diagnosticos_col.find().sort('data', -1).limit(50))
        
        # Obter avaliações detalhadas
        avaliacoes_col = db.get_collection('avaliacoes_detalhes')
        avaliacoes_detalhes = list(avaliacoes_col.find().sort('created_at', -1).limit(50))
        
        # Obter eventos de integração
        eventos_col = db.get_collection('eventos_integracao')
        eventos_integracao = list(eventos_col.find().sort('created_at', -1).limit(50))
        # Normalizar campos esperados pelo template
        def _normalize_manutencao_doc(m):
            # created_at pode ser 'created_at' ou 'data' ou 'timestamp'
            if not m.get('created_at'):
                m['created_at'] = m.get('data') or m.get('timestamp')
            # tempo_execucao_minutos vs tempo_execucao
            if not m.get('tempo_execucao_minutos'):
                m['tempo_execucao_minutos'] = m.get('tempo_execucao') or m.get('duracao_minutos') or None
            return m

        def _normalize_diagnostico_doc(d):
            # created_at/timestamp
            if not d.get('created_at'):
                d['created_at'] = d.get('data') or d.get('timestamp')
            # duracao_minutos normalization
            if not d.get('duracao_minutos'):
                d['duracao_minutos'] = d.get('duracao_diagnostico_minutos') or d.get('duracao') or None
            # dados_obd expected by template
            if d.get('scanner_data') and d['scanner_data'].get('parametros_live'):
                d['dados_obd'] = d['scanner_data']['parametros_live']
            return d

        def _normalize_avaliacao_doc(a):
            if not a.get('created_at'):
                a['created_at'] = a.get('data_avaliacao') or a.get('created_at') or None
            return a

        manutencoes = [_normalize_manutencao_doc(m) for m in manutencoes]
        diagnosticos = [_normalize_diagnostico_doc(d) for d in diagnosticos]
        avaliacoes_detalhes = [_normalize_avaliacao_doc(a) for a in avaliacoes_detalhes]
        # Garantir que cada doc tenha um identificador string para usar nos templates (doc_id)
        for m in manutencoes:
            if m.get('_id'):
                try:
                    m['doc_id'] = str(m.get('_id'))
                except Exception:
                    m['doc_id'] = None
            else:
                m['doc_id'] = None
        for d in diagnosticos:
            if d.get('_id'):
                try:
                    d['doc_id'] = str(d.get('_id'))
                except Exception:
                    d['doc_id'] = None
            else:
                d['doc_id'] = None
        for a in avaliacoes_detalhes:
            if a.get('_id'):
                try:
                    a['doc_id'] = str(a.get('_id'))
                except Exception:
                    a['doc_id'] = None
            else:
                a['doc_id'] = None
        for e in eventos_integracao:
            if e.get('_id'):
                try:
                    e['doc_id'] = str(e.get('_id'))
                except Exception:
                    e['doc_id'] = None
            else:
                e['doc_id'] = None
        # Normalizar destinos de eventos: se forem IDs/strings, transformar em objects simples
        for e in eventos_integracao:
            destinos = e.get('destinos') or []
            normalized = []
            for destino in destinos:
                if isinstance(destino, dict):
                    normalized.append(destino)
                else:
                    # destino pode ser ObjectId ou string -> apresentar como URL bruto
                    normalized.append({
                        'sistema': '',
                        'url': str(destino),
                        'status': 'pendente',
                        'http_status': None,
                        'response_body': None,
                        'processado_em': None,
                        'tempo_resposta_ms': None
                    })
            e['destinos'] = normalized
        # Mapear `ordem_servico_id` para um nome amigável nas avaliações
        ordem_ids = set()
        for a in avaliacoes_detalhes:
            if a.get('ordem_servico_id'):
                try:
                    ordem_ids.add(int(a.get('ordem_servico_id')))
                except Exception:
                    pass
        ordens_dict = {}
        if ordem_ids:
            ords = OrdemServico.objects.filter(ordem_servico_id__in=ordem_ids)
            for o in ords:
                ordens_dict[o.ordem_servico_id] = str(o)
        # Anexar `ordem_servico_nome` às avaliações para uso no template
        for a in avaliacoes_detalhes:
            oid = a.get('ordem_servico_id')
            try:
                oid_int = int(oid) if oid is not None else None
            except Exception:
                oid_int = None
            a['ordem_servico_nome'] = ordens_dict.get(oid_int) if oid_int else None

        # Attach cliente_nome to avaliacoes if missing by resolving cliente_id from PostgreSQL
        cliente_ids = set()
        for a in avaliacoes_detalhes:
            cid = a.get('cliente_id')
            if cid is not None:
                try:
                    cliente_ids.add(int(cid))
                except Exception:
                    pass

        if cliente_ids:
            clientes_qs = Cliente.objects.filter(cliente_id__in=cliente_ids)
            clientes_map = {c.cliente_id: c.c_nome for c in clientes_qs}
            for a in avaliacoes_detalhes:
                if not a.get('cliente_nome'):
                    cid = a.get('cliente_id')
                    try:
                        cid_int = int(cid) if cid is not None else None
                    except Exception:
                        cid_int = None
                    if cid_int and cid_int in clientes_map:
                        a['cliente_nome'] = clientes_map[cid_int]

        # Fallbacks adicionais: tentar resolver a partir de `conta_id` ou `criado_por` (email)
        for a in avaliacoes_detalhes:
            if a.get('cliente_nome'):
                continue
            # conta_id may refer to Utilizador.user_id or PK
            conta_id = a.get('conta_id')
            resolved = None
            if conta_id is not None:
                try:
                    conta_int = int(conta_id)
                except Exception:
                    conta_int = None
                if conta_int is not None:
                    try:
                        util = Utilizador.objects.filter(user_id=conta_int).first()
                        if not util:
                            util = Utilizador.objects.filter(pk=conta_int).first()
                        if util:
                            if getattr(util, 'cliente', None):
                                resolved = util.cliente.c_nome
                            else:
                                # recorrer ao nome a partir dos campos do utilizador (p.ex. email)
                                resolved = getattr(util, 'email', None)
                    except Exception:
                        resolved = None

            # tentar `criado_por` que pode conter um email
            if not resolved:
                criado_por = a.get('criado_por') or a.get('created_by')
                if criado_por and isinstance(criado_por, str) and '@' in criado_por:
                    try:
                        util = Utilizador.objects.filter(email=criado_por).first()
                        if util and util.cliente:
                            resolved = util.cliente.c_nome
                        elif util:
                            resolved = util.email
                    except Exception:
                        resolved = None

            if resolved:
                a['cliente_nome'] = resolved
        
    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        messages.warning(request, 'Não foi possível conectar ao MongoDB.')
    
    # Coletar IDs únicos de carros para buscar detalhes
    carro_ids = set()
    for m in manutencoes:
        if m.get('carro_id'):
            carro_ids.add(m['carro_id'])
    for d in diagnosticos:
        if d.get('carro_id'):
            carro_ids.add(d['carro_id'])
    
    # Buscar detalhes dos carros
    carros_dict = {}
    if carro_ids:
        carros = Carro.objects.filter(carro_id__in=carro_ids)
        for carro in carros:
            carros_dict[carro.carro_id] = carro
    
    # Anexar objeto carro aos registros de manutenção
    for m in manutencoes:
        if m.get('carro_id') and m['carro_id'] in carros_dict:
            m['carro_obj'] = carros_dict[m['carro_id']]
        else:
            m['carro_obj'] = None
    
    # Anexar objeto carro aos registros de diagnóstico
    for d in diagnosticos:
        if d.get('carro_id') and d['carro_id'] in carros_dict:
            d['carro_obj'] = carros_dict[d['carro_id']]
        else:
            d['carro_obj'] = None
    
    # Verificar permissões do utilizador
    user_role = None
    try:
        utilizador = Utilizador.objects.get(email=request.user.email)
        user_role = utilizador.role
    except Utilizador.DoesNotExist:
        pass
    
    # Staff tem acesso completo, clientes só podem ver/adicionar avaliações
    pode_ver_tudo = user_role in ['admin', 'gerente', 'funcionario', 'mecanico']
    eh_cliente = user_role == 'cliente'
    
    # Preparar listas para formulários (Avaliação e Eventos) baseadas no perfil
    form_carros_list = []
    form_ordens_list = []
    # id do cliente para pré-preenchimento nos formulários de evento/avaliação
    evento_cliente_id = None
    
    if eh_cliente:
        # Cliente: Apenas seus carros (comprados) e suas ordens de serviço
        try:
            # Obter cliente_id do utilizador
            cliente_obj = Cliente.objects.get(utilizador__email=request.user.email)
            evento_cliente_id = cliente_obj.cliente_id
            
            # Carros comprados pelo cliente
            carros_ids = Venda.objects.filter(cliente=cliente_obj).values_list('carro_id', flat=True)
            form_carros_list = Carro.objects.filter(carro_id__in=carros_ids)
            
            # Ordens de serviço do cliente
            form_ordens_list = OrdemServico.objects.filter(cliente=cliente_obj).order_by('-data_entrada')
        except Cliente.DoesNotExist:
            pass
    else:
        # Admin/Staff: Todos os carros e ordens
        form_carros_list = Carro.objects.all().order_by('marca', 'modelo')
        form_ordens_list = OrdemServico.objects.all().order_by('-data_entrada')

    # Expor todos os carros para seleção em formulários quando staff/admin
    carros_para_form = Carro.objects.all().order_by('marca', 'modelo') if pode_ver_tudo else []

    context = {
        'manutencoes': manutencoes if pode_ver_tudo else [],
        'diagnosticos': diagnosticos if pode_ver_tudo else [],
        'avaliacoes_detalhes': avaliacoes_detalhes,
        'eventos_integracao': eventos_integracao if pode_ver_tudo else [],
        # `carros` usado pelo template nas sections de manutenção/diagnóstico
        'carros': carros_para_form,
        'mecanicos': Mecanico.objects.all().order_by('nome') if pode_ver_tudo else [],
        'clientes': get_clientes_list(),
        'form_carros_list': form_carros_list,
        'form_ordens_list': form_ordens_list,
        # Compatibilidade com template atual: evento_carros usado no formulário de eventos
        'evento_carros': form_carros_list if form_carros_list else carros_para_form,
        # Preencher nome do cliente (para eventos/avaliações) quando for cliente
        'evento_cliente_nome': (request.user.get_full_name() or request.user.email) if eh_cliente else None,
        'evento_cliente_id': evento_cliente_id,
        'pode_ver_tudo': pode_ver_tudo,
        'eh_cliente': eh_cliente,
        'user_role': user_role,
    }
    return render(request, 'oficina.html', context)


@login_required
@user_passes_test(is_staff_user)
def eliminar_manutencao_view(request, doc_id):
    if request.method == 'POST':
        try:
            from .mongo import HistoricoManutencao
            ok = HistoricoManutencao.eliminar_por_id(doc_id)
            if ok:
                messages.success(request, 'Registo de manutenção eliminado com sucesso.')
            else:
                messages.error(request, 'Não foi possível eliminar o registo de manutenção.')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar manutenção: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def eliminar_diagnostico_view(request, doc_id):
    if request.method == 'POST':
        try:
            from .mongo import DiagnosticosOficina
            ok = DiagnosticosOficina.eliminar_por_id(doc_id)
            if ok:
                messages.success(request, 'Diagnóstico eliminado com sucesso.')
            else:
                messages.error(request, 'Não foi possível eliminar o diagnóstico.')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar diagnóstico: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def eliminar_avaliacao_detalhe_view(request, doc_id):
    if request.method == 'POST':
        try:
            from .mongo import AvaliacoesDetalhes
            ok = AvaliacoesDetalhes.eliminar_por_id(doc_id)
            if ok:
                messages.success(request, 'Detalhe de avaliação eliminado com sucesso.')
            else:
                messages.error(request, 'Não foi possível eliminar o detalhe da avaliação.')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar detalhe de avaliação: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def eliminar_evento_view(request, evento_id):
    if request.method == 'POST':
        try:
            from .mongo import EventosIntegracao
            ok = EventosIntegracao.eliminar_evento(evento_id)
            if ok:
                messages.success(request, 'Evento eliminado com sucesso.')
            else:
                messages.error(request, 'Não foi possível eliminar o evento.')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar evento: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def atualizar_status_evento_view(request, evento_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            from .mongo import EventosIntegracao
            ok = EventosIntegracao.set_status(evento_id, new_status)
            if ok:
                messages.success(request, 'Status do evento atualizado.')
            else:
                messages.error(request, 'Não foi possível atualizar o status do evento.')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar status: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def atualizar_status_destino_view(request, evento_id, destino_index):
    if request.method == 'POST':
        novo_status = request.POST.get('destino_status')
        http_status = request.POST.get('http_status')
        try:
            http_status_val = int(http_status) if http_status else None
        except Exception:
            http_status_val = None
        try:
            from .mongo import EventosIntegracao
            ok = EventosIntegracao.set_destino_status(evento_id, int(destino_index), novo_status, http_status_val, None)
            if ok:
                messages.success(request, 'Status do destino atualizado.')
            else:
                messages.error(request, 'Não foi possível atualizar o destino.')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar destino: {e}')
    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def adicionar_manutencao_view(request):
    # Adicionar registo de manutenção ao MongoDB
    if request.method == 'POST':
        try:
            from .mongo import HistoricoManutencao
            from datetime import datetime

            carro_id_str = request.POST.get('carro_id', '').strip()
            carro_id = int(carro_id_str) if carro_id_str else 0
            ordem_servico_id_str = request.POST.get('ordem_servico_id', '').strip()
            ordem_servico_id = int(ordem_servico_id_str) if ordem_servico_id_str else None

            # Obter dados do mecânico do banco PostgreSQL
            try:
                mecanico_id_str = request.POST.get('mecanico_id', '').strip()
                if mecanico_id_str:
                    mecanico_obj = Mecanico.objects.get(mecanico_id=int(mecanico_id_str))
                mecanico_data = {
                    'mecanico_id': mecanico_obj.mecanico_id,
                    'nome': mecanico_obj.nome,
                    'especialidade': mecanico_obj.especialidade
                }
            except (Mecanico.DoesNotExist, ValueError):
                mecanico_data = {
                    'mecanico_id': 0,
                    'nome': request.POST.get('mecanico_nome', 'Técnico Externo'),
                    'especialidade': request.POST.get('especialidade', 'Geral')
                }

            # Preparar peças utilizadas (se fornecidas)
            pecas_utilizadas = []
            pecas_ids = request.POST.getlist('peca_id[]')
            pecas_nomes = request.POST.getlist('peca_nome[]')
            pecas_quantidades = request.POST.getlist('peca_quantidade[]')
            pecas_codigos = request.POST.getlist('peca_codigo[]')
            pecas_precos = request.POST.getlist('peca_preco[]')

            for i in range(len(pecas_ids)):
                if pecas_ids[i] and pecas_nomes[i]:
                    pecas_utilizadas.append({
                        'peca_id': int(pecas_ids[i]) if pecas_ids[i].isdigit() else 0,
                        'nome': pecas_nomes[i],
                        'quantidade': float(pecas_quantidades[i]) if i < len(pecas_quantidades) and pecas_quantidades[i] else 1,
                        'codigo': pecas_codigos[i] if i < len(pecas_codigos) and pecas_codigos[i] else '',
                        'preco_unitario': float(pecas_precos[i]) if i < len(pecas_precos) and pecas_precos[i] else 0
                    })

            # Dados de diagnóstico
            diagnostico_data = {
                'descricao': request.POST.get('diagnostico_descricao', ''),
                'quilometragem': int(request.POST.get('quilometragem', 0) or 0),
                'nivel_urgencia': request.POST.get('nivel_urgencia', 'baixo'),
                'observacoes': request.POST.get('observacoes', '')
            }

            # Anexos (se fornecidos)
            anexos = []
            anexo_tipos = request.POST.getlist('anexo_tipo[]')
            anexo_urls = request.POST.getlist('anexo_url[]')
            anexo_descricoes = request.POST.getlist('anexo_descricao[]')

            for i in range(len(anexo_tipos)):
                if anexo_tipos[i] and anexo_urls[i]:
                    anexos.append({
                        'tipo': anexo_tipos[i],
                        'url': anexo_urls[i],
                        'descricao': anexo_descricoes[i] if i < len(anexo_descricoes) else ''
                    })

            custo_total = float(request.POST.get('custo_total', 0) or 0)
            tempo_execucao = int(request.POST.get('tempo_execucao', 60) or 60)
            proxima_revisao_str = request.POST.get('proxima_revisao', '').strip()
            proxima_revisao = int(proxima_revisao_str) if proxima_revisao_str else None

            # Inserir usando a classe MongoDB
            registro_id = HistoricoManutencao.inserir_registro(
                carro_id=carro_id,
                ordem_servico_id=ordem_servico_id,
                descricao=request.POST.get('descricao'),
                mecanico=mecanico_data,
                pecas_utilizadas=pecas_utilizadas,
                diagnostico=diagnostico_data,
                custo_total=custo_total,
                tempo_execucao_minutos=tempo_execucao,
                proxima_revisao_km=proxima_revisao,
                anexos=anexos
            )

            messages.success(request, f'Manutenção registada com sucesso! ID: {registro_id}')
        except Exception as e:
            logger.error(f"Erro ao registar manutenção: {e}")
            messages.error(request, f'Erro ao registar manutenção: {str(e)}')

    return redirect('oficina')


@login_required
@user_passes_test(is_staff_user)
def adicionar_diagnostico_view(request):
    # Adicionar diagnóstico ao MongoDB
    if request.method == 'POST':
        try:
            from .mongo import DiagnosticosOficina
            from datetime import datetime

            carro_id_str = request.POST.get('carro_id', '').strip()
            carro_id = int(carro_id_str) if carro_id_str else 0
            ordem_servico_id_str = request.POST.get('ordem_servico_id', '').strip()
            ordem_servico_id = int(ordem_servico_id_str) if ordem_servico_id_str else None

            # Dados do scanner OBD-II
            scanner_data = {
                'marca_scanner': request.POST.get('marca_scanner', 'OBD-II Scanner'),
                'protocolo': request.POST.get('protocolo', 'ISO 15765-4 (CAN)'),
                'vin': request.POST.get('vin', ''),
                'dtcs': [],  # Códigos de erro DTC
                'parametros_live': {
                    'rpm': int(request.POST.get('rpm', 0) or 0),
                    'temperatura_motor': float(request.POST.get('temperatura_motor', 0) or 0),
                    'temperatura_ar_admissao': float(request.POST.get('temperatura_ar', 20) or 20),
                    'velocidade': int(request.POST.get('velocidade', 0) or 0),
                    'nivel_combustivel': int(request.POST.get('nivel_combustivel', 100) or 100),
                    'pressao_oleo': float(request.POST.get('pressao_oleo', 0) or 0),
                    'voltagem_bateria': float(request.POST.get('voltagem_bateria', 12.6) or 12.6),
                    'tempo_motor_ligado': int(request.POST.get('tempo_motor_ligado', 0) or 0)
                },
                'readiness_monitors': {
                    'catalyst': request.POST.get('catalyst_status', 'ready'),
                    'oxygen_sensor': request.POST.get('oxygen_sensor_status', 'ready'),
                    'evaporative_system': request.POST.get('evaporative_status', 'ready'),
                    'egr_system': request.POST.get('egr_status', 'ready'),
                    'misfire': request.POST.get('misfire_status', 'ready'),
                    'comprehensive': request.POST.get('comprehensive_status', 'ready')
                }
            }

            # Adicionar códigos DTC se fornecidos
            dtc_codigos = request.POST.getlist('dtc_codigo[]')
            dtc_descricoes = request.POST.getlist('dtc_descricao[]')
            dtc_status = request.POST.getlist('dtc_status[]')

            for i in range(len(dtc_codigos)):
                if dtc_codigos[i]:
                    scanner_data['dtcs'].append({
                        'codigo': dtc_codigos[i],
                        'descricao': dtc_descricoes[i] if i < len(dtc_descricoes) else '',
                        'status': dtc_status[i] if i < len(dtc_status) else 'active',
                        'odometro': int(request.POST.get('quilometragem', 0) or 0),
                        'data_deteccao': datetime.now()
                    })

            # Códigos de erro identificados
            codigos_erro = []
            codigos = request.POST.getlist('codigo_erro[]')
            descricoes_tecnicas = request.POST.getlist('descricao_tecnica[]')
            gravidades = request.POST.getlist('gravidade[]')
            causas = request.POST.getlist('causas[]')

            for i in range(len(codigos)):
                if codigos[i]:
                    codigos_erro.append({
                        'codigo': codigos[i],
                        'tipo': request.POST.get('tipo_erro', 'powertrain'),
                        'gravidade': gravidades[i] if i < len(gravidades) else 'moderada',
                        'descricao_tecnica': descricoes_tecnicas[i] if i < len(descricoes_tecnicas) else '',
                        'causas_possiveis': causas[i].split(',') if i < len(causas) and causas[i] else [],
                        'impacto': request.POST.get('impacto', '')
                    })

            # Recomendações
            recomendacoes = []
            prioridades = request.POST.getlist('prioridade[]')
            descricoes_rec = request.POST.getlist('recomendacao_descricao[]')
            custos_est = request.POST.getlist('custo_estimado[]')
            prazos = request.POST.getlist('prazo[]')
            pecas_nec = request.POST.getlist('pecas_necessarias[]')

            for i in range(len(descricoes_rec)):
                if descricoes_rec[i]:
                    recomendacoes.append({
                        'prioridade': prioridades[i] if i < len(prioridades) else 'media',
                        'descricao': descricoes_rec[i],
                        'custo_estimado': float(custos_est[i]) if i < len(custos_est) and custos_est[i] else 0,
                        'prazo': prazos[i] if i < len(prazos) else '1_semana',
                        'pecas_necessarias': pecas_nec[i].split(',') if i < len(pecas_nec) and pecas_nec[i] else []
                    })

            # Dados do mecânico
            mecanico_data = None
            try:
                mecanico_id_str = request.POST.get('mecanico_id', '').strip()
                if mecanico_id_str:
                    mecanico_obj = Mecanico.objects.get(mecanico_id=int(mecanico_id_str))
                    mecanico_data = {
                        'mecanico_id': mecanico_obj.mecanico_id,
                        'nome': mecanico_obj.nome,
                        'especialidade': mecanico_obj.especialidade,
                        'certificacoes': []  # Pode ser expandido depois
                    }
                else:
                    mecanico_data = {
                        'mecanico_id': 0,
                        'nome': request.POST.get('mecanico_nome', 'Técnico Externo'),
                        'especialidade': request.POST.get('especialidade', 'Diagnóstico'),
                        'certificacoes': []
                    }
            except (Mecanico.DoesNotExist, ValueError):
                mecanico_data = {
                    'mecanico_id': 0,
                    'nome': request.POST.get('mecanico_nome', 'Técnico Externo'),
                    'especialidade': request.POST.get('especialidade', 'Diagnóstico'),
                    'certificacoes': []
                }

            duracao_diagnostico = int(request.POST.get('duracao_diagnostico', 30) or 30)

            # Inserir usando a classe MongoDB
            registro_id = DiagnosticosOficina.inserir_diagnostico(
                ordem_servico_id=ordem_servico_id,
                carro_id=carro_id,
                scanner_data=scanner_data,
                codigos_erro=codigos_erro,
                recomendacoes=recomendacoes,
                mecanico=mecanico_data,
                duracao_diagnostico_minutos=duracao_diagnostico
            )

            messages.success(request, f'Diagnóstico registado com sucesso! ID: {registro_id}')
        except Exception as e:
            logger.error(f"Erro ao registar diagnóstico: {e}")
            messages.error(request, f'Erro ao registar diagnóstico: {str(e)}')

    return redirect('oficina')


@login_required
def adicionar_avaliacao_view(request):
    # Adicionar avaliação detalhada ao MongoDB
    if request.method == 'POST':
        try:
            from .mongo import AvaliacoesDetalhes

            tipo_avaliacao = request.POST.get('tipo_avaliacao', 'servico')
            classificacao = int(request.POST.get('classificacao', 5))
            cliente_nome = request.POST.get('cliente_nome', '').strip()
            ordem_servico_id = request.POST.get('ordem_servico_id')
            comentario = request.POST.get('comentario', '').strip()
            detalhes = request.POST.get('detalhes', '').strip()

            # Obter o cliente_id baseado no utilizador logado
            user_role = get_user_role_by_email(request.user.email)
            cliente_id = None
            cliente_nome = ""

            if user_role == 'cliente':
                # Se for cliente, obter o cliente_id pelo email do utilizador
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.cliente_id
                        FROM utilizadores u
                        JOIN clientes c ON u.cliente_id = c.cliente_id
                        WHERE u.email = %s
                    """, [request.user.email])
                    result = cursor.fetchone()
                    if result:
                        cliente_id = result[0]
                
                # Validação de Segurança: Verificar se a OS pertence ao cliente
                if ordem_servico_id:
                    os_check = OrdemServico.objects.filter(ordem_servico_id=ordem_servico_id, cliente_id=cliente_id).exists()
                    if not os_check:
                        messages.error(request, 'Só pode avaliar as suas próprias ordens de serviço.')
                        return redirect('oficina')
                
                # Auto-preencher nome (visível apenas para admin no backend)
                if request.user.first_name:
                    cliente_nome = f"{request.user.first_name} {request.user.last_name}".strip()
                else:
                    cliente_nome = request.user.email
            else:
                # Se for staff, pode especificar o cliente pela dropdown ou pelo nome
                cliente_id_sel = request.POST.get('cliente_id')
                if cliente_id_sel:
                    try:
                        cliente_obj = Cliente.objects.get(cliente_id=int(cliente_id_sel))
                        cliente_id = cliente_obj.cliente_id
                        cliente_nome = cliente_obj.c_nome
                    except Exception:
                        cliente_id = None
                else:
                    # fallback para nome livre (compatibilidade)
                    cliente_nome = request.POST.get('cliente_nome', '').strip()
                    if cliente_nome:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT cliente_id FROM clientes
                                WHERE c_nome ILIKE %s
                                LIMIT 1
                            """, [f'%{cliente_nome}%'])
                            result = cursor.fetchone()
                            if result:
                                cliente_id = result[0]

            # Integração Automática de Dados (Substitui JSON manual)
            detalhes_integrados = {}
            if ordem_servico_id:
                try:
                    os_obj = OrdemServico.objects.select_related('tipo_servico', 'mecanico').get(ordem_servico_id=ordem_servico_id)
                    detalhes_integrados = {
                        "veiculo": os_obj.nome_veiculo,
                        "servico": os_obj.tipo_servico.nome,
                        "data_entrada": str(os_obj.data_entrada),
                        "data_saida": str(os_obj.data_saida) if os_obj.data_saida else None,
                        "mecanico": os_obj.mecanico.nome if os_obj.mecanico else "Não atribuído",
                        "valor_total": float(os_obj.valor_total) if os_obj.valor_total else 0.0,
                        "origem_dados": "PostgreSQL Integration"
                    }
                except OrdemServico.DoesNotExist:
                    pass

            # Preparar dados da avaliação
            avaliacao_data = {
                'tipo_avaliacao': tipo_avaliacao,
                'classificacao': classificacao,
                'cliente_id': cliente_id,
                'cliente_nome': cliente_nome,
                'conta_id': getattr(request.user, 'id', None),
                'comentario': comentario,
                'detalhes': detalhes,
                'detalhes': detalhes_integrados, # Dados integrados automaticamente
                'data_avaliacao': datetime.now(),
            }

            # Adicionar ordem de serviço se fornecida
            if ordem_servico_id:
                try:
                    avaliacao_data['ordem_servico_id'] = int(ordem_servico_id)
                except ValueError:
                    pass

            # Inserir usando a classe MongoDB
            avaliacao_id = AvaliacoesDetalhes.inserir(avaliacao_data)

            messages.success(request, f'Avaliação registada com sucesso! ID: {avaliacao_id}')
        except Exception as e:
            logger.error(f"Erro ao registar avaliação: {e}")
            messages.error(request, f'Erro ao registar avaliação: {str(e)}')

    return redirect('oficina')


@login_required
@user_passes_test(lambda u: get_user_role_by_email(u.email) in ['admin', 'gerente', 'funcionario', 'mecanico'])
def adicionar_evento_view(request):
    # Adicionar evento de serviço na oficina ao MongoDB (apenas admin/gerente)
    # Adicionar evento de serviço na oficina ao MongoDB
    # Acesso: Admin/Gerente (qualquer carro) ou Cliente (apenas seus carros)
    if request.method == 'POST':
        try:
            from .mongo import EventosIntegracao

            # nome do campo no formulário: tipo_evento
            tipo = request.POST.get('tipo_evento', request.POST.get('tipo', 'servico_oficina'))
            descricao = request.POST.get('descricao', '').strip()
            ordem_servico_id = request.POST.get('ordem_servico_id')
            cliente_id = request.POST.get('cliente_id')
            carro_id = request.POST.get('carro_id') # Usado para validação de propriedade
            prioridade = request.POST.get('prioridade', 'normal')
            status = request.POST.get('status', 'pendente')

            user_role = get_user_role_by_email(request.user.email)
            cliente_id = None

            if user_role == 'cliente':
                # Lógica para Cliente
                try:
                    cliente_obj = Cliente.objects.get(utilizador__email=request.user.email)
                    cliente_id = cliente_obj.cliente_id
                    
                    # Validação: Cliente só pode criar evento para seus carros
                    if carro_id:
                        dono_carro = Venda.objects.filter(carro_id=carro_id, cliente_id=cliente_id).exists()
                        if not dono_carro:
                            messages.error(request, 'Só pode criar eventos para carros que comprou.')
                            return redirect('oficina')
                    
                    # Forçar status inicial para clientes
                    status = 'pendente'
                    prioridade = 'normal' # Clientes não definem prioridade alta
                except Cliente.DoesNotExist:
                    messages.error(request, 'Perfil de cliente não encontrado.')
                    return redirect('oficina')
            else:
                # Lógica para Admin/Gerente
                # Pode definir cliente_id manualmente se vier do form, ou deixar vazio
                cliente_id_form = request.POST.get('cliente_id')
                if cliente_id_form:
                    cliente_id = int(cliente_id_form)

            # Preparar payload
            payload = {
                'descricao': descricao,
                'prioridade': prioridade,
                'status': status,
                'data_criacao': datetime.now()
            }

            if ordem_servico_id:
                try:
                    payload['ordem_servico_id'] = int(ordem_servico_id)
                except ValueError:
                    pass

            if carro_id:
                payload['carro_id'] = int(carro_id)

            if cliente_id:
                try:
                    payload['cliente_id'] = int(cliente_id)
                except ValueError:
                    pass
                payload['cliente_id'] = cliente_id

            # Destinos a partir do formulário (listas de campos)
            destinos = []
            destino_urls = request.POST.getlist('destino_url[]') or request.POST.getlist('destino_url')
            destino_sistemas = request.POST.getlist('destino_sistema[]') or request.POST.getlist('destino_sistema')
            destino_statuses = request.POST.getlist('destino_status[]') or request.POST.getlist('destino_status')
            if destino_urls:
                for idx, url in enumerate(destino_urls):
                    sistema = (destino_sistemas[idx] if idx < len(destino_sistemas) else '') or 'externo'
                    dst_status = (destino_statuses[idx] if idx < len(destino_statuses) else '') or 'pendente'
                    destinos.append({
                        'sistema': sistema,
                        'url': url,
                        'status': dst_status,
                        'http_status': None,
                        'response_body': None,
                        'processado_em': None,
                        'tempo_resposta_ms': None
                    })
            # fallback para um destino padrão se nenhum foi fornecido
            if not destinos:
                destinos = [{
                    'url': 'https://api.interna.oficina/webhook',
                    'metodo': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'status': 'pendente'
                }]

            # Criar evento usando a classe MongoDB
            evento_id = EventosIntegracao.criar_evento(
                tipo=tipo,
                payload=payload,
                destinos=destinos,
                max_retries=3
            )

            # Adicionar campos extras
            evento_doc = {
                'sistema_origem': 'oficina',
                'data_evento': datetime.now(),
                'criado_por': request.user.email
            }

            # Atualizar o documento com campos adicionais
            from .mongo import eventos_integracao_col
            eventos_integracao_col().update_one(
                {'evento_id': evento_id},
                {'$set': evento_doc}
            )

            messages.success(request, f'Evento de serviço criado com sucesso! ID: {evento_id}')
        except Exception as e:
            logger.error(f"Erro ao criar evento de serviço: {e}")
            messages.error(request, f'Erro ao criar evento: {str(e)}')

    return redirect('oficina')


# =============================
# Importação/Exportação JSON (apenas admin)
# =============================

@login_required
@user_passes_test(is_superuser)
def import_export_view(request):
    # Página de import/export JSON
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        ficheiro = request.FILES.get('ficheiro')
        
        if ficheiro:
            try:
                dados = json.load(ficheiro)
                registros = dados.get('dados', [])
                
                if tipo == 'clientes':
                    imported = 0
                    skipped = 0
                    errors = []
                    with connection.cursor() as cursor:
                        for idx, cliente in enumerate(registros, start=1):
                            try:
                                cid = cliente.get('cliente_id')
                                nome = cliente.get('c_nome')
                                email = cliente.get('c_email')
                                telefone = cliente.get('c_telefone')
                                nif = cliente.get('nif')
                                data_cadastro = cliente.get('data_cadastro') if cliente.get('data_cadastro') else None
                                data_nascimento = cliente.get('data_nascimento') if cliente.get('data_nascimento') else None

                                if cid is not None:
                                    # Inserir com ID explícito
                                    try:
                                        cursor.execute(
                                            "INSERT INTO clientes (cliente_id, c_nome, c_email, c_telefone, nif, data_cadastro, data_nascimento) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                            [cid, nome, email, telefone, nif, data_cadastro, data_nascimento]
                                        )
                                    except Exception as e:
                                        skipped += 1
                                        errors.append(f'Registro {idx}: falha ao inserir cliente_id {cid} - {str(e)}')
                                        continue
                                else:
                                    # Utilizar procedure como alternativa para inserção normal
                                    cursor.execute("CALL sp_inserir_cliente(%s, %s, %s, %s, %s)", [
                                        nome,
                                        email,
                                        telefone,
                                        nif,
                                        data_nascimento
                                    ])

                                imported += 1
                            except Exception as e:
                                skipped += 1
                                errors.append(f'Registro {idx}: exceção ao processar cliente - {str(e)}')
                                continue

                        # After batch, ensure sequence is in sync when explicit IDs were used
                        try:
                            cursor.execute("SELECT setval(pg_get_serial_sequence('clientes','cliente_id'), COALESCE((SELECT MAX(cliente_id) FROM clientes), 1), true)")
                        except Exception:
                            pass

                    if imported:
                        messages.success(request, f'{imported} clientes importados com sucesso.')
                    if skipped:
                        preview = '\n'.join(errors[:10])
                        messages.error(request, f'{skipped} clientes ignorados. Exemplos: {preview}')

                elif tipo == 'carros':
                    imported = 0
                    skipped = 0
                    errors = []
                    with connection.cursor() as cursor:
                        for idx, carro in enumerate(registros, start=1):
                            try:
                                cid = carro.get('carro_id')
                                stand_id = carro.get('stand_id')
                                marca_id = carro.get('marca_id')
                                modelo = carro.get('modelo')
                                ano = carro.get('ano')
                                preco = carro.get('preco') if carro.get('preco') is not None else carro.get('preço')
                                estado = carro.get('estado', 'novo')
                                quilometragem = carro.get('quilometragem') if carro.get('quilometragem') is not None else 0
                                cor = carro.get('cor')
                                chassi = carro.get('chassi')
                                placa = carro.get('placa')
                                combustivel = carro.get('combustivel')
                                potencia = carro.get('potencia')
                                ref_imagem_capa = carro.get('ref_imagem_capa')

                                if cid is not None:
                                    try:
                                        cursor.execute(
                                            "INSERT INTO carros (carro_id, stand_id, marca_id, modelo, ano, \"preço\", estado, quilometragem, cor, chassi, placa, combustivel, potencia, ref_imagem_capa) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                                [cid, stand_id, marca_id, modelo, ano, preco, estado, quilometragem, cor, chassi, placa, combustivel, potencia, ref_imagem_capa]
                                        )
                                    except Exception as e:
                                        skipped += 1
                                        errors.append(f'Registro {idx}: falha ao inserir carro_id {cid} - {str(e)}')
                                        continue
                                else:
                                    # Use stored procedure when no explicit ID
                                    cursor.execute("CALL sp_inserir_carro(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [
                                        stand_id,
                                        marca_id,
                                        modelo,
                                        ano,
                                        preco,
                                        estado,
                                        quilometragem,
                                        cor,
                                        chassi,
                                        placa,
                                        combustivel,
                                        potencia,
                                        ref_imagem_capa
                                    ])

                                imported += 1
                            except Exception as e:
                                skipped += 1
                                errors.append(f'Registro {idx}: exceção ao processar carro - {str(e)}')
                                continue

                        # Sincronizar sequência da tabela `carros`
                        try:
                            cursor.execute("SELECT setval(pg_get_serial_sequence('carros','carro_id'), COALESCE((SELECT MAX(carro_id) FROM carros), 1), true)")
                        except Exception:
                            pass

                    if imported:
                        messages.success(request, f'{imported} carros importados com sucesso.')
                    if skipped:
                        preview = '\n'.join(errors[:10])
                        messages.error(request, f'{skipped} carros ignorados. Exemplos: {preview}')

                elif tipo == 'vendas':
                    imported = 0
                    skipped = 0
                    errors = []
                    for idx, venda in enumerate(registros, start=1):
                        try:
                            reasons = []

                            cliente_id = venda.get('cliente_id')
                            if not cliente_id:
                                cliente_nome = venda.get('cliente') or venda.get('cliente_nome')
                                if cliente_nome:
                                    with connection.cursor() as cursor:
                                        cursor.execute("SELECT cliente_id FROM clientes WHERE c_nome = %s LIMIT 1", [cliente_nome])
                                        row = cursor.fetchone()
                                        cliente_id = row[0] if row else None

                            carro_id = venda.get('carro_id')
                            if not carro_id:
                                carro_modelo = venda.get('carro')
                                marca = venda.get('marca')
                                if carro_modelo:
                                    with connection.cursor() as cursor:
                                        if marca:
                                            cursor.execute(
                                                "SELECT c.carro_id FROM carros c JOIN marcas m ON c.marca_id = m.marca_id WHERE c.modelo = %s AND m.m_nome = %s LIMIT 1",
                                                [carro_modelo, marca]
                                            )
                                        else:
                                            cursor.execute("SELECT carro_id FROM carros WHERE modelo = %s LIMIT 1", [carro_modelo])
                                        row = cursor.fetchone()
                                        carro_id = row[0] if row else None

                            funcionario_id = venda.get('funcionario_id')
                            if not funcionario_id:
                                funcionario_nome = venda.get('funcionario')
                                if funcionario_nome:
                                    with connection.cursor() as cursor:
                                        cursor.execute("SELECT funcionario_id FROM funcionarios WHERE f_nome = %s LIMIT 1", [funcionario_nome])
                                        row = cursor.fetchone()
                                        funcionario_id = row[0] if row else None

                            preco_final = venda.get('preco_final') or venda.get('preco')
                            data_str = venda.get('data')
                            data_val = None
                            if data_str:
                                try:
                                    data_val = datetime.fromisoformat(data_str)
                                except Exception:
                                    try:
                                        data_val = datetime.strptime(data_str, '%Y-%m-%d')
                                    except Exception:
                                        data_val = None

                            # Validate existence of foreign keys in DB and required fields
                            with connection.cursor() as cursor:
                                # Cliente: if ID provided but missing, try to resolve by name/email
                                if cliente_id:
                                    cursor.execute("SELECT 1 FROM clientes WHERE cliente_id = %s", [cliente_id])
                                    if not cursor.fetchone():
                                        # Try to resolve by name or email from the venda record
                                        cliente_nome = venda.get('cliente') or venda.get('cliente_nome')
                                        cliente_email = venda.get('cliente_email') or venda.get('email')
                                        resolved = None
                                        if cliente_email:
                                            cursor.execute("SELECT cliente_id FROM clientes WHERE c_email = %s LIMIT 1", [cliente_email])
                                            row = cursor.fetchone()
                                            resolved = row[0] if row else None
                                        if not resolved and cliente_nome:
                                            cursor.execute("SELECT cliente_id FROM clientes WHERE c_nome = %s LIMIT 1", [cliente_nome])
                                            row = cursor.fetchone()
                                            resolved = row[0] if row else None
                                        if resolved:
                                            cliente_id = resolved
                                        else:
                                            reasons.append(f"cliente_id {cliente_id} não existe e não foi possível resolver por nome/email")
                                else:
                                    reasons.append("cliente_id ausente")

                                # Carro: if ID provided but missing, try to resolve by modelo/marca/chassi/placa
                                if carro_id:
                                    cursor.execute("SELECT 1 FROM carros WHERE carro_id = %s", [carro_id])
                                    if not cursor.fetchone():
                                        carro_modelo = venda.get('carro') or venda.get('modelo')
                                        marca = venda.get('marca')
                                        chassi = venda.get('chassi')
                                        placa = venda.get('placa')
                                        resolved = None
                                        if placa:
                                            cursor.execute("SELECT carro_id FROM carros WHERE placa = %s LIMIT 1", [placa])
                                            row = cursor.fetchone()
                                            resolved = row[0] if row else None
                                        if not resolved and chassi:
                                            cursor.execute("SELECT carro_id FROM carros WHERE chassi = %s LIMIT 1", [chassi])
                                            row = cursor.fetchone()
                                            resolved = row[0] if row else None
                                        if not resolved and carro_modelo:
                                            if marca:
                                                cursor.execute(
                                                    "SELECT c.carro_id FROM carros c JOIN marcas m ON c.marca_id = m.marca_id WHERE c.modelo = %s AND m.m_nome = %s LIMIT 1",
                                                    [carro_modelo, marca]
                                                )
                                            else:
                                                cursor.execute("SELECT carro_id FROM carros WHERE modelo = %s LIMIT 1", [carro_modelo])
                                            row = cursor.fetchone()
                                            resolved = row[0] if row else None
                                        if resolved:
                                            carro_id = resolved
                                        else:
                                            reasons.append(f"carro_id {carro_id} não existe e não foi possível resolver por modelo/marca/chassi/placa")
                                else:
                                    reasons.append("carro_id ausente")

                            if not preco_final:
                                reasons.append("preco_final ausente")

                            if reasons:
                                skipped += 1
                                errors.append(f'Registro {idx}: ' + '; '.join(reasons))
                                continue

                            # Use stored procedure to register venda (updates carro status, reservations)
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "CALL sp_registar_venda(%s, %s, %s, %s, %s)",
                                    [cliente_id, carro_id, preco_final, funcionario_id, venda.get('forma_pagamento')]
                                )
                            imported += 1
                        except Exception as e:
                            skipped += 1
                            errors.append(f'Registro {idx}: exceção ao inserir - {str(e)}')

                    if imported:
                        messages.success(request, f'{imported} vendas importadas com sucesso.')
                    if skipped:
                        # show up to 10 error lines
                        preview = '\n'.join(errors[:10])
                        messages.error(request, f'{skipped} registos ignorados. Exemplos: {preview}')
                
            except Exception as e:
                messages.error(request, f'Erro ao importar: {str(e)}')
    
    return render(request, 'import_export.html')


@login_required
@user_passes_test(is_superuser)
def exportar_carros_view(request):
    # Exportar carros para JSON
    try:
        with connection.cursor() as cursor:
            # Export all columns from carros for fidelity with DB schema
            cursor.execute("SELECT * FROM carros")
            columns = [col[0] for col in cursor.description]
            carros = [dict(zip(columns, row)) for row in cursor.fetchall()]
            # Keep original column names (including 'preço') to preserve localized export
            # Importer accepts both 'preco' and 'preço'.
        
        dados = {
            'tipo': 'carros',
            'total': len(carros),
            'data_exportacao': str(datetime.now()),
            'dados': carros
        }
        
        response = HttpResponse(
            json.dumps(dados, indent=2, default=str, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="carros.json"'
        return response
    except Exception as e:
        messages.error(request, f'Erro ao exportar: {str(e)}')
        return redirect('import_export')


@login_required
@user_passes_test(is_superuser)
def exportar_clientes_view(request):
    # Exportar clientes para JSON
    try:
        with connection.cursor() as cursor:
            # Export raw clientes table so import can recreate full attributes
            cursor.execute("SELECT * FROM clientes")
            columns = [col[0] for col in cursor.description]
            clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        dados = {
            'tipo': 'clientes',
            'total': len(clientes),
            'data_exportacao': str(datetime.now()),
            'dados': clientes
        }
        
        response = HttpResponse(
            json.dumps(dados, indent=2, default=str, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="clientes.json"'
        return response
    except Exception as e:
        messages.error(request, f'Erro ao exportar: {str(e)}')
        return redirect('import_export')


@login_required
@user_passes_test(is_superuser)
def exportar_vendas_view(request):
    # Exportar vendas para JSON
    try:
        with connection.cursor() as cursor:
            # Export raw vendas table to include all fields available
            cursor.execute("SELECT * FROM vendas")
            columns = [col[0] for col in cursor.description]
            vendas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        dados = {
            'tipo': 'vendas',
            'total': len(vendas),
            'data_exportacao': str(datetime.now()),
            'dados': vendas
        }
        
        response = HttpResponse(
            json.dumps(dados, indent=2, default=str, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="vendas.json"'
        return response
    except Exception as e:
        messages.error(request, f'Erro ao exportar: {str(e)}')
        return redirect('import_export')


# =============================
# Secção de ordens de serviço
# =============================

@login_required
def ordens_servico_view(request):
    # Página de gestão de ordens de serviço
    if request.method == 'POST':
        try:
            # Debug: mostrar todos os dados recebidos
            print("DEBUG - Dados recebidos no POST:")
            for key, value in request.POST.items():
                print(f"  {key}: '{value}'")

            # Validar campos obrigatórios
            cliente_id_str = request.POST.get('cliente_id', '').strip()
            nome_veiculo = request.POST.get('nome_veiculo', '').strip()  # Substituindo carro_id
            tipo_servico_id_str = request.POST.get('tipo_servico_id', '').strip()
            quilometragem_str = request.POST.get('quilometragem', '').strip()
            valor_mao_obra_str = request.POST.get('valor_mao_obra', '').strip()

            if not cliente_id_str:
                raise ValueError("Cliente é obrigatório")
            if not nome_veiculo:
                raise ValueError("Nome do veículo é obrigatório")
            if not tipo_servico_id_str:
                raise ValueError("Tipo de serviço é obrigatório")
            if not quilometragem_str:
                raise ValueError("Quilometragem é obrigatória")
            if not valor_mao_obra_str:
                raise ValueError("Valor da mão de obra é obrigatório")

            # Criar nova ordem de serviço
            cliente_id = int(cliente_id_str)
            tipo_servico_id = int(tipo_servico_id_str)
            quilometragem = int(quilometragem_str)
            valor_mao_obra = float(valor_mao_obra_str)
            mecanico_id = request.POST.get('mecanico_id', '').strip()
            baia_id = request.POST.get('baia_id', '').strip()
            prioridade = request.POST.get('prioridade', 'normal')
            data_prevista = request.POST.get('data_prevista')
            diagnostico = request.POST.get('diagnostico', '')
            observacoes = request.POST.get('observacoes', '')

            # Converter IDs para objetos
            cliente = Cliente.objects.get(cliente_id=cliente_id)
            tipo_servico = TipoServico.objects.get(tipo_servico_id=tipo_servico_id)

            mecanico = None
            if mecanico_id:
                try:
                    mecanico = Mecanico.objects.get(mecanico_id=int(mecanico_id))
                except (ValueError, Mecanico.DoesNotExist):
                    pass  # Mantém None se inválido

            baia = None
            if baia_id:
                try:
                    baia = BaiaOficina.objects.get(baia_id=int(baia_id))
                except (ValueError, BaiaOficina.DoesNotExist):
                    pass  # Mantém None se inválido

            # Obter o utilizador que está criando a ordem
            try:
                utilizador_criador = Utilizador.objects.get(email=request.user.email)
            except Utilizador.DoesNotExist:
                messages.error(request, 'Utilizador não encontrado.')
                return redirect('ordens_servico')

            # Criar ordem de serviço
            ordem = OrdemServico.objects.create(
                cliente=cliente,
                nome_veiculo=nome_veiculo,  # Substituindo carro
                tipo_servico=tipo_servico,
                mecanico=mecanico,
                baia=baia,
                prioridade=prioridade,
                descricao_problema=diagnostico,
                observacoes=observacoes,
                valor_total=valor_mao_obra,
                criado_por=utilizador_criador
            )

            # Nota: Não atualizamos quilometragem do carro pois não temos mais referência ao carro

            messages.success(request, f'Ordem de serviço #{ordem.ordem_servico_id} criada com sucesso!')
            return redirect('ordens_servico')

        except Exception as e:
            messages.error(request, f'Erro ao criar ordem de serviço: {str(e)}')
            return redirect('ordens_servico')

    # GET - mostrar página
    try:
        # Obter o utilizador logado
        try:
            utilizador_logado = Utilizador.objects.get(email=request.user.email)
            user_role = utilizador_logado.role
        except Utilizador.DoesNotExist:
            user_role = None

        # Filtrar ordens baseado no role
        if user_role in ['admin', 'gerente', 'mecanico']:
            # Admin, gerente e mecânico veem todas as ordens
            ordens = OrdemServico.objects.filter(
                status__in=['pendente', 'em_andamento']
            ).select_related('cliente', 'tipo_servico').order_by('-data_entrada')

            ordens_atrasadas = OrdemServico.objects.filter(
                data_prevista_saida__lt=timezone.now(),
                status__in=['pendente', 'em_andamento']
            ).select_related('cliente').order_by('data_prevista_saida')

            ordens_concluidas = OrdemServico.objects.filter(
                status='concluida'
            ).select_related('cliente', 'tipo_servico').order_by('-data_saida')
        elif user_role == 'funcionario':
            # Funcionário vê todas as ordens (pode ver tudo)
            ordens = OrdemServico.objects.filter(
                status__in=['pendente', 'em_andamento']
            ).select_related('cliente', 'tipo_servico').order_by('-data_entrada')

            ordens_atrasadas = OrdemServico.objects.filter(
                data_prevista_saida__lt=timezone.now(),
                status__in=['pendente', 'em_andamento']
            ).select_related('cliente').order_by('data_prevista_saida')

            ordens_concluidas = OrdemServico.objects.filter(
                status='concluida'
            ).select_related('cliente', 'tipo_servico').order_by('-data_saida')
        elif user_role == 'cliente':
            # Cliente vê apenas suas próprias ordens
            ordens = OrdemServico.objects.filter(
                status__in=['pendente', 'em_andamento'],
                cliente__utilizador=utilizador_logado
            ).select_related('cliente', 'tipo_servico').order_by('-data_entrada')

            ordens_atrasadas = OrdemServico.objects.filter(
                data_prevista_saida__lt=timezone.now(),
                status__in=['pendente', 'em_andamento'],
                cliente__utilizador=utilizador_logado
            ).select_related('cliente').order_by('data_prevista_saida')

            ordens_concluidas = OrdemServico.objects.filter(
                status='concluida',
                cliente__utilizador=utilizador_logado
            ).select_related('cliente', 'tipo_servico').order_by('-data_saida')
        else:
            # Utilizador sem role definido vê apenas as suas próprias ordens (como cliente)
            ordens = OrdemServico.objects.filter(
                status__in=['pendente', 'em_andamento'],
                cliente__utilizador=utilizador_logado
            ).select_related('cliente', 'tipo_servico').order_by('-data_entrada')

            ordens_atrasadas = OrdemServico.objects.filter(
                data_prevista_saida__lt=timezone.now(),
                status__in=['pendente', 'em_andamento'],
                cliente__utilizador=utilizador_logado
            ).select_related('cliente').order_by('data_prevista_saida')

            ordens_concluidas = OrdemServico.objects.filter(
                status='concluida',
                cliente__utilizador=utilizador_logado
            ).select_related('cliente', 'tipo_servico').order_by('-data_saida')

        context = {
            'ordens': ordens,
            'ordens_atrasadas': ordens_atrasadas,
            'ordens_concluidas': ordens_concluidas,
            'clientes': Cliente.objects.all().order_by('c_nome'),
            'tipos_servico': TipoServico.objects.all().order_by('nome'),
            'mecanicos': Mecanico.objects.all().order_by('nome'),
            'baias': BaiaOficina.objects.all().order_by('numero_baia'),
            'user_role': user_role,
        }
        return render(request, 'ordens_servico.html', context)

    except Exception as e:
        messages.error(request, f'Erro ao carregar ordens de serviço: {str(e)}')
        return render(request, 'ordens_servico.html', {
            'ordens': [],
            'ordens_atrasadas': [],
            'ordens_concluidas': [],
            'clientes': [],
            'tipos_servico': [],
            'mecanicos': [],
            'baias': [],
            'user_role': user_role,
        })


@login_required
def concluir_ordem_servico_view(request, ordem_id):
    # Concluir uma ordem de serviço
    # Verificar se o utilizador tem permissão (apenas oficina)
    try:
        utilizador = Utilizador.objects.get(email=request.user.email)
        if utilizador.role not in ['admin', 'gerente', 'mecanico']:
            messages.error(request, 'Não tem permissão para concluir ordens de serviço.')
            return redirect('ordens_servico')
    except Utilizador.DoesNotExist:
        messages.error(request, 'Utilizador não encontrado.')
        return redirect('ordens_servico')

    if request.method == 'POST':
        try:
            ordem = OrdemServico.objects.get(ordem_servico_id=ordem_id)
            ordem.status = 'concluida'
            ordem.data_saida = timezone.now().date()
            ordem.save()

            messages.success(request, f'Ordem de serviço #{ordem_id} concluída com sucesso!')
        except OrdemServico.DoesNotExist:
            messages.error(request, 'Ordem de serviço não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro ao concluir ordem: {str(e)}')

    return redirect('ordens_servico')


@login_required
def cancelar_ordem_servico_view(request, ordem_id):
    # Cancelar uma ordem de serviço
    # Verificar se o utilizador tem permissão (apenas oficina)
    try:
        utilizador = Utilizador.objects.get(email=request.user.email)
        if utilizador.role not in ['admin', 'gerente', 'mecanico']:
            messages.error(request, 'Não tem permissão para cancelar ordens de serviço.')
            return redirect('ordens_servico')
    except Utilizador.DoesNotExist:
        messages.error(request, 'Utilizador não encontrado.')
        return redirect('ordens_servico')

    if request.method == 'POST':
        try:
            ordem = OrdemServico.objects.get(ordem_servico_id=ordem_id)
            ordem.status = 'cancelada'
            ordem.save()

            messages.success(request, f'Ordem de serviço #{ordem_id} cancelada.')
        except OrdemServico.DoesNotExist:
            messages.error(request, 'Ordem de serviço não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro ao cancelar ordem: {str(e)}')

    return redirect('ordens_servico')


@login_required
def detalhes_ordem_servico_view(request, ordem_id):
    # Página de detalhes de uma ordem de serviço específica
    try:
        # Buscar dados básicos da ordem no PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM vw_ordem_servico_detalhes WHERE ordem_servico_id = %s",
                [ordem_id]
            )
            row = cursor.fetchone()
            if not row:
                messages.error(request, 'Ordem de serviço não encontrada.')
                return redirect('ordens_servico')

            columns = [col[0] for col in cursor.description]
            ordem = dict(zip(columns, row))
        
        # Buscar peças utilizadas (se houver)
        pecas_utilizadas = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM vw_servico_pecas WHERE ordem_servico_id = %s", [ordem_id])
                columns = [col[0] for col in cursor.description]
                pecas_utilizadas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Erro ao buscar peças: {e}")
        
        # Buscar dados do MongoDB (diagnósticos, histórico de manutenção)
        diagnosticos = []
        historico_manutencao = []
        
        try:
            from .mongo import DiagnosticosOficina, HistoricoManutencao
            
            # Diagnósticos
            diagnosticos = DiagnosticosOficina.buscar_por_ordem_servico(ordem_id) or []
            if diagnosticos:
                diagnosticos = [diagnosticos] if isinstance(diagnosticos, dict) else diagnosticos
            
            # Histórico de manutenção
            historico_manutencao = HistoricoManutencao.buscar_por_ordem_servico(ordem_id) or []
            
        except Exception as e:
            logger.warning(f"Erro ao buscar dados MongoDB: {e}")
        
        # Verificar permissões (cliente só vê suas próprias ordens)
        user_role = None
        try:
            utilizador = Utilizador.objects.get(email=request.user.email)
            user_role = utilizador.role
        except Utilizador.DoesNotExist:
            pass
            
        pode_editar = user_role in ['admin', 'gerente', 'mecanico']
        eh_cliente_dono = (user_role == 'cliente' and 
                          Utilizador.objects.filter(
                              email=request.user.email, 
                              cliente_id=ordem['cliente_id']
                          ).exists())
        
        if not (pode_editar or eh_cliente_dono):
            messages.error(request, 'Não tem permissão para ver esta ordem de serviço.')
            return redirect('ordens_servico')
        
        context = {
            'ordem': ordem,
            'pecas_utilizadas': pecas_utilizadas,
            'diagnosticos': diagnosticos,
            'historico_manutencao': historico_manutencao,
            'pode_editar': pode_editar,
            'eh_cliente_dono': eh_cliente_dono,
            'user_role': user_role,
        }
        
        return render(request, 'detalhes_ordem_servico.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao carregar detalhes da ordem: {e}")
        messages.error(request, f'Erro ao carregar detalhes: {str(e)}')
        return redirect('ordens_servico')


@login_required
def avaliar_ordem_servico_view(request, ordem_id):
    # Avaliar uma ordem de serviço (apenas clientes donos da ordem)
    try:
        # Verificar se a ordem existe e se o utilizador é o dono
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    os.ordem_servico_id,
                    os.cliente_id,
                    os.status,
                    c.c_nome
                FROM ordens_servico os
                JOIN clientes c ON os.cliente_id = c.cliente_id
                WHERE os.ordem_servico_id = %s
            """, [ordem_id])
            
            row = cursor.fetchone()
            if not row:
                messages.error(request, 'Ordem de serviço não encontrada.')
                return redirect('ordens_servico')
                
            ordem_servico_id, cliente_id, status, cliente_nome = row
            
            # Verificar se a ordem está concluída
            if status != 'concluida':
                messages.error(request, 'Apenas ordens concluídas podem ser avaliadas.')
                return redirect('detalhes_ordem_servico', ordem_id=ordem_id)
            
            # Verificar se o utilizador é o cliente dono da ordem
            try:
                utilizador = Utilizador.objects.get(email=request.user.email)
                if utilizador.role != 'cliente' or utilizador.cliente_id != cliente_id:
                    messages.error(request, 'Não tem permissão para avaliar esta ordem de serviço.')
                    return redirect('ordens_servico')
            except Utilizador.DoesNotExist:
                messages.error(request, 'Utilizador não encontrado.')
                return redirect('ordens_servico')
        
        if request.method == 'POST':
            classificacao = request.POST.get('classificacao')
            comentario = request.POST.get('comentario', '').strip()
            fotos = request.FILES.getlist('fotos')
            
            # Validar classificação
            try:
                classificacao = int(classificacao)
                if classificacao < 1 or classificacao > 5:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, 'Classificação inválida.')
                return redirect('detalhes_ordem_servico', ordem_id=ordem_id)
            
            # Salvar avaliação no MongoDB
            try:
                from .mongo import AvaliacoesDetalhes
                
                # Preparar dados da avaliação
                avaliacao_data = {
                    'ordem_servico_id': ordem_id,
                    'cliente_id': cliente_id,
                    'cliente_nome': cliente_nome,
                    'classificacao': classificacao,
                    'comentario': comentario,
                    'tipo_avaliacao': 'servico',
                    'timestamp': datetime.now(),
                }
                
                # Processar fotos se houver
                if fotos:
                    fotos_urls = []
                    for foto in fotos:
                        try:
                            # Salvar foto no Azure Blob Storage
                            blob_name = f"avaliacoes/{ordem_id}/{foto.name}"
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            success = loop.run_until_complete(update_file(foto, blob_name, 'avaliacoes'))
                            
                            if success:
                                # Gerar SAS URL para acesso
                                sas_url = generate_sas_url(blob_name, 'avaliacoes')
                                fotos_urls.append({
                                    'nome': foto.name,
                                    'url': sas_url,
                                    'blob_name': blob_name
                                })
                        except Exception as e:
                            logger.error(f"Erro ao salvar foto {foto.name}: {e}")
                    
                    if fotos_urls:
                        avaliacao_data['fotos'] = fotos_urls
                
                # Salvar avaliação
                avaliacao_id = AvaliacoesDetalhes.inserir(avaliacao_data)
                
                if avaliacao_id:
                    messages.success(request, 'Avaliação enviada com sucesso!')
                else:
                    messages.error(request, 'Erro ao salvar avaliação.')
                
            except Exception as e:
                logger.error(f"Erro ao salvar avaliação: {e}")
                messages.error(request, 'Erro ao salvar avaliação.')
            
            return redirect('detalhes_ordem_servico', ordem_id=ordem_id)
        
        # Se não for POST, redirecionar para detalhes
        return redirect('detalhes_ordem_servico', ordem_id=ordem_id)
        
    except Exception as e:
        logger.error(f"Erro ao processar avaliação: {e}")
        messages.error(request, f'Erro ao processar avaliação: {str(e)}')
        return redirect('ordens_servico')


@login_required
def eliminar_ordem_servico_view(request, ordem_id):
    # Eliminar uma ordem de serviço concluída (apenas admin, gerente, mecanico)
    if request.method == 'POST':
        try:
            # Verificar permissões
            utilizador = Utilizador.objects.get(email=request.user.email)
            if utilizador.role not in ['admin', 'gerente', 'mecanico']:
                messages.error(request, 'Não tem permissão para eliminar ordens de serviço.')
                return redirect('ordens_servico')
            
            # Verificar se a ordem existe e está concluída
            ordem = OrdemServico.objects.get(ordem_servico_id=ordem_id)
            if ordem.status != 'concluida':
                messages.error(request, 'Apenas ordens concluídas podem ser eliminadas.')
                return redirect('ordens_servico')
            
            # Chamar o procedimento armazenado
            with connection.cursor() as cursor:
                cursor.execute("CALL sp_eliminar_os(%s)", [ordem_id])
            
            messages.success(request, f'Ordem de serviço #{ordem_id} eliminada com sucesso!')
            
        except OrdemServico.DoesNotExist:
            messages.error(request, 'Ordem de serviço não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro ao eliminar ordem de serviço: {str(e)}')
    
    return redirect('ordens_servico')
