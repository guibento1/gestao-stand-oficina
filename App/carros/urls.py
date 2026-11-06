from django.urls import path
from . import views

urlpatterns = [
    # ========== PÁGINAS PÚBLICAS ==========
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('avaliacoes/', views.avaliacoes_view, name='avaliacoes'),
    path('avaliacoes/eliminar/<int:avaliacao_id>/', views.eliminar_avaliacao_view, name='eliminar_avaliacao'),
    
    # ========== CARROS ==========
    path('carros/', views.carros_view, name='carros'),
    path('carros/<int:carro_id>/', views.detalhes_carro_view, name='detalhes_carro'),
    path('carros/editar/<int:carro_id>/', views.editar_carro_view, name='editar_carro'),
    path('carros/eliminar/<int:carro_id>/', views.eliminar_carro_view, name='eliminar_carro'),
    path('carros/upload-imagem/<int:carro_id>/', views.upload_imagem_carro_view, name='upload_imagem_carro'),
    path('carros/eliminar-imagem/<int:imagem_id>/', views.eliminar_imagem_carro_view, name='eliminar_imagem_carro'),
    
    # ========== CLIENTES ==========
    path('clientes/', views.clientes_view, name='clientes'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente_view, name='editar_cliente'),
    path('clientes/eliminar/<int:cliente_id>/', views.eliminar_cliente_view, name='eliminar_cliente'),
    
    # ========== VENDAS ==========
    path('vendas/', views.vendas_view, name='vendas'),
    path('vendas/eliminar/<int:venda_id>/', views.eliminar_venda_view, name='eliminar_venda'),
    
    # ========== RESERVAS ==========
    path('reservas/', views.reservas_view, name='reservas'),
    path('reservas/editar/<int:reserva_id>/', views.editar_reserva_view, name='editar_reserva'),
    path('reservas/eliminar/<int:reserva_id>/', views.eliminar_reserva_view, name='eliminar_reserva'),
    
    # ========== OFICINA (MongoDB) ==========
    path('oficina/', views.oficina_view, name='oficina'),
    path('oficina/manutencao/', views.adicionar_manutencao_view, name='adicionar_manutencao'),
    path('oficina/diagnostico/', views.adicionar_diagnostico_view, name='adicionar_diagnostico'),
    path('oficina/avaliacao/', views.adicionar_avaliacao_view, name='adicionar_avaliacao'),
    path('oficina/evento/', views.adicionar_evento_view, name='adicionar_evento'),
    path('oficina/manutencao/eliminar/<str:doc_id>/', views.eliminar_manutencao_view, name='eliminar_manutencao'),
    path('oficina/diagnostico/eliminar/<str:doc_id>/', views.eliminar_diagnostico_view, name='eliminar_diagnostico'),
    path('oficina/avaliacao/eliminar/<str:doc_id>/', views.eliminar_avaliacao_detalhe_view, name='eliminar_avaliacao_detalhe'),
    path('oficina/evento/eliminar/<str:evento_id>/', views.eliminar_evento_view, name='eliminar_evento'),
    path('oficina/evento/atualizar-status/<str:evento_id>/', views.atualizar_status_evento_view, name='atualizar_status_evento'),
    path('oficina/evento/atualizar-destino/<str:evento_id>/<int:destino_index>/', views.atualizar_status_destino_view, name='atualizar_status_destino'),
    
    # ========== ORDENS DE SERVIÇO ==========
    path('ordens-servico/', views.ordens_servico_view, name='ordens_servico'),
    path('ordens-servico/<int:ordem_id>/', views.detalhes_ordem_servico_view, name='detalhes_ordem_servico'),
    path('ordens-servico/avaliar/<int:ordem_id>/', views.avaliar_ordem_servico_view, name='avaliar_ordem_servico'),
    path('ordens-servico/concluir/<int:ordem_id>/', views.concluir_ordem_servico_view, name='concluir_os'),
    path('ordens-servico/cancelar/<int:ordem_id>/', views.cancelar_ordem_servico_view, name='cancelar_os'),
    path('ordens-servico/eliminar/<int:ordem_id>/', views.eliminar_ordem_servico_view, name='eliminar_ordem_servico'),
    
    # ========== IMPORT/EXPORT (apenas admin) ==========
    path('import-export/', views.import_export_view, name='import_export'),
    path('exportar/carros/', views.exportar_carros_view, name='exportar_carros'),
    path('exportar/clientes/', views.exportar_clientes_view, name='exportar_clientes'),
    path('exportar/vendas/', views.exportar_vendas_view, name='exportar_vendas'),
]
