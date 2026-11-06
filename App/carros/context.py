from django.db import connection


def user_role_context(request):
    """Adiciona a role do utilizador ao contexto de todos os templates"""
    context = {
        'user_role': None,
        'pode_gerir_clientes': False,
        'pode_gerir_vendas': False,
        'pode_editar_carros': False,
        'pode_editar_clientes': False,
        'pode_aceder_oficina': False,
    }
    
    if request.user.is_authenticated:
        # Obter role da sessão ou da BD
        role = request.session.get('user_role')
        
        if not role:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT role FROM utilizadores WHERE email = %s", [request.user.email])
                    row = cursor.fetchone()
                    if row:
                        role = row[0]
                        request.session['user_role'] = role
            except Exception:
                pass
        
        context['user_role'] = role
        # Funcionário pode ver clientes mas não editar/eliminar
        context['pode_gerir_clientes'] = role in ['admin', 'gerente', 'funcionario']
        # Funcionário pode registar vendas
        context['pode_gerir_vendas'] = role in ['admin', 'gerente', 'funcionario']
        # Apenas gerente e admin podem editar/eliminar carros
        context['pode_editar_carros'] = role in ['admin', 'gerente']
        # Apenas gerente e admin podem editar/eliminar clientes
        context['pode_editar_clientes'] = role in ['admin', 'gerente']
        # Oficina: gerente, admin e mecânico, funcionário e cliente
        context['pode_aceder_oficina'] = role in ['admin', 'gerente', 'mecanico', 'funcionario', 'cliente']
    
    return context
