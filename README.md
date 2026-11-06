# Mapa de Tabelas, Métodos e Coleções — Stand de Carros com Oficina

**Grupo 34:**

- Guilherme Bento - 25193
- Lucas Santos - 27440
- Tiago Rebelo - 25216

---

## A) PostgreSQL

## Tabela: stands

**Responsável:** Guilherme

| **Nome**                                             | **Descrição**                                                                          | **Stakeholder** | **Requisito**        |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------- | -------------------- |
| [View] vw_stands_oficina (Simples)                   | Lista stands com capacidade de oficina.                                                | Admin           | Gestão de recursos   |
|                                                      |                                                                                        |                 |                      |
| [Função] fn_exportar_relatorio_financeiro (mes, ano) | Exporta receitas, custos e lucro por stand para contabilidade.                         | Admin           | Exportação de dados  |
| [View] vw_stock_atual (Materializada)                | Mostra a contagem de carros por estado (disponível, reservado, vendido) em cada stand. | Gerente         | Gestão de inventário |

---

## Tabela: marcas

**Responsável:** Lucas

| Nome | Descrição                   | Stakeholder | Requisito |
| ---- | --------------------------- | ----------- | --------- |
| —    | Tabela de marcas de carros. | —           | —         |

---

## Tabela: servico_pecas

**Responsável:** Lucas

| Nome                              | Descrição                                                                                         | Stakeholder    | Requisito                     |
|:--------------------------------- |:------------------------------------------------------------------------------------------------- |:-------------- |:----------------------------- |
| [View] vw_servico_pecas (Simples) | Lista detalhada de todas as peças consumidas por ordem de serviço, com custos unitários e totais. | Mecânico/Admin | **Rastreabilidade de custos** |

--- 

## Tabela: tipos_servico

**Responsável:** Lucas

| Nome                                             | Descrição                                                              | Stakeholder | Requisito                |
| ------------------------------------------------ | ---------------------------------------------------------------------- | ----------- | ------------------------ |
| [View] vw_servicos_mais_vendidos (Materializada) | Ranking dos serviços mais solicitados e valor total faturado por tipo. | Gerente     | Análise de rentabilidade |

---

## Tabela: pecas_acessorios

**Responsável:** Lucas

| **Nome**                              | **Descrição**                                                | **Stakeholder** | **Requisito**        |
| ------------------------------------- | ------------------------------------------------------------ | --------------- | -------------------- |
| [View] vw_pecas_stock_baixo (Simples) | Lista peças com stock abaixo do mínimo definido.             | Gerente         | Gestão de Inventário |
| [Trigger] tg_pecas_stock_alert        | Lança aviso automático quando o stock atinge o nível mínimo. | Gerente         |                      |

---

## Tabela: carros

**Responsável:** Lucas

| Nome                                      | Descrição                                                                      | Stakeholder | Requisito                        |
| ----------------------------------------- | ------------------------------------------------------------------------------ | ----------- | -------------------------------- |
| [Procedure] sp_inserir_carro              | Insere carro (stand, marca, modelo, ano, preço, estado, quilometragem, etc.).  | Admin       | Adicionar stock ao catálogo      |
| [Procedure] sp_eliminar_carro             | Remove um carro do sistema (validando dependências).                           | Admin       | Remoção de inventário            |
| [Procedure] sp_atualizar_carro            | Atualiza todos os dados técnicos, preço e estado de um carro existente.        | Gerente     | Atualização de catálogo          |
| [View] vw_carros_disponiveis (Simples)    | Lista carros disponíveis (não reservados nem vendidos) com imagem de capa.     | Cliente     | Catálogo correto para o frontend |
| [View] vw_carros_completos (Simples)      | Lista todos os carros com marca, stand e informações completas.                | Funcionário | Gestão completa de inventário    |
| [Função] fn_carro_disponivel (carro_id)   | Retorna se o carro não está vendido nem reservado.                             | Funcionário | Validação central para vendas    |
| [Função] fn_exportar_inventario_carros () | Exporta inventário completo de carros (stock, preços, status) para auditorias. | Admin       | Exportação de dados              |
| [Trigger] tg_carros_before_delete         | Impede apagar carro com vendas ou garantias associadas.                        | Admin       | Preservar histórico legal        |

---

## Tabela: imagens_carros

**Responsável:** Guilherme

| Nome                                       | Descrição                                                                               | Stakeholder | Requisito                |
| ------------------------------------------ | --------------------------------------------------------------------------------------- | ----------- | ------------------------ |
| [Função] fn_gerar_url_imagem (blob_name)   | Gera URL completa do Azure a partir do nome do blob.                                    | Frontend    | Acesso direto às imagens |
| [Trigger] tg_limitar_imagens_carro         | Limita número máximo de imagens por carro (20).                                         | Funcionário | Performance e storage    |
| [Trigger] tg_imagens_carro_atualizar_capa  | Garante apenas 1 imagem marcada como capa por carro.                                    | Funcionário | Consistência da galeria  |
| [View] vw_imagens_carros_galeria (Simples) | Lista imagens da galeria com URLs geradas automaticamente (ordenadas por capa e ordem). | Cliente     | Visualização da galeria  |
| [Procedure] sp_inserir_imagem_carro        | Regista nova imagem associada a um carro (blob, descrição e flag de capa).              | Funcionário | Gestão de multimédia     |
| [Procedure] sp_atualizar_imagem_carro      | Atualiza metadados da imagem (ordem, descrição ou define como capa).                    | Funcionário | Organização da galeria   |
| [Procedure] sp_eliminar_imagem_carro       | Remove o registo da imagem da base de dados.                                            | Admin       | Limpeza de armazenamento |

---

## Tabela: baias_oficina

**Responsável:** Tiago

| Nome                                             | Descrição                              | Stakeholder | Requisito                |
| ------------------------------------------------ | -------------------------------------- | ----------- | ------------------------ |
| [View] vw_baias_disponiveis (Simples)            | Lista baias com status = 'disponivel'. | Funcionário | Alocação rápida          |
| [Função] fn_baia_disponivel (baia_id, data_hora) | Verifica se baia está livre.           | Funcionário | Validação de agendamento |

---

## Tabela: funcionarios

**Responsável:** Guilherme

| Nome                                              | Descrição                                                                | Stakeholder | Requisito               |
| ------------------------------------------------- | ------------------------------------------------------------------------ | ----------- | ----------------------- |
| [View] vw_funcionarios_desempenho (Materializada) | Agrega o total de vendas e valor faturado por funcionário.               | Gerente     | Avaliação de desempenho |
| [View] vw_funcionarios_vendas (Simples)           | Relatório detalhado de vendas com dados do funcionário, cliente e carro. | Admin       | Relatório consolidado   |

---

## Tabela: gerentes

**Responsável:** Tiago

| Nome | Descrição           | Stakeholder | Requisito |
| ---- | ------------------- | ----------- | --------- |
|      | Tabela de gerentes. |             |           |

---

## Tabela: mecanicos

**Responsável:** Tiago

| Nome                                            | Descrição                                                                     | Stakeholder | Requisito             |
| ----------------------------------------------- | ----------------------------------------------------------------------------- | ----------- | --------------------- |
| [View] vw_mecanicos_disponibilidade (Simples)   | Mostra mecânicos e ordens de serviço atuais.                                  | Funcionário | Alocação eficiente    |
| [View] vw_mecanicos_desempenho  (Materializada) | Calcula OS concluídas, faturação total e tempo médio de serviço por mecânico. | Gerente     | Eficiência da oficina |

---

## Tabela: admins

**Responsável:** Tiago

| Nome | Descrição         | Stakeholder | Requisito         |
| ---- | ----------------- | ----------- | ----------------- |
| —    | Tabela de admins. | Admin       | Gestão de sistema |

---

## Tabela: clientes

**Responsável:** Guilherme

| Nome                                        | Descrição                                                                  | Stakeholder | Requisito                       |
| ------------------------------------------- | -------------------------------------------------------------------------- | ----------- | ------------------------------- |
| [Procedure] sp_inserir_cliente              | Insere cliente (nome, email, telefone, NIF).                               | Funcionário | Cadastro rápido e consistente   |
| [Procedure] sp_eliminar_cliente             | Remove a ficha de um cliente e anonimiza dados sensíveis se necessário.    | Admin       | Gestão de contas / RGPD         |
| [Procedure] sp_atualizar_cliente            | Atualiza dados de contacto e pessoais de um cliente.                       | Funcionário | Manutenção de CRM               |
| [Procedure] sp_atualizar_ref_imagem_capa    | Define uma imagem específica como a capa (destaque) do carro.              | Funcionário | Personalização de anúncio       |
| [Procedure] sp_limpar_ref_imagem_capa       | Remove a referência de capa do carro (ex: quando a imagem capa é apagada). | Sistema     | Integridade de dados            |
| [View] vw_clientes_detalhes (Materializada) | Lista clientes com dados completos e estatísticas de vendas.               | Funcionário | Consulta detalhada de clientes  |
| [View] vw_clientes_compras (Materializada)  | Lista clientes e número de vendas.                                         | Admin       | Relatório direto de clientes    |
| [Função] fn_validar_nif (text)              | Validação de NIF reutilizável (CHECK/rotinas).                             | Admin       | Integridade de dados de cliente |
| [Trigger] tg_clientes_validar_email         | Valida formato e normaliza email (lowercase) antes de inserir/atualizar.   | Admin       | Integridade de dados            |

---

## Tabela: Utilizadores

**Responsável:** Guilherme

| Nome                                                | Descrição                                                                                     | Stakeholder | Requisito                |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------- | ------------------------ |
| [Função] fn_autenticar_utilizador (email, password) | Valida credenciais comparando a hash da password e retorna ID/Role se válido.                 | Sistema     | Segurança e Autenticação |
| [Procedure] sp_atualizar_last_login                 | Atualiza o carimbo de data/hora do último acesso bem-sucedido do utilizador.                  | Sistema     | Auditoria de segurança   |
| [View] vw_clientes_utilizadores (Simples)           | Relaciona os dados de perfil do cliente com a respetiva conta de utilizador (login e estado). | Admin       | Gestão de contas         |

---

## Tabela: ordens_servico

**Responsável:** Tiago

| **Nome**                                      | **Descrição**                                                                           | **Stakeholder** | **Requisito**                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------- | --------------- | --------------------------------- |
| [View] vw_ordem_servico_detalhes (Simples)    | Agrega todos os dados da OS (cliente, veículo, mecânico, peças) para a ficha detalhada. | Funcionário     | **Consulta detalhada de serviço** |
| [View] vw_ordens_servico_concluidas (Simples) | Lista apenas as ordens de serviço finalizadas e fechadas.                               | Admin/Mecânico  | Histórico de reparações           |

## Tabela: reservas

**Responsável:** Lucas

| Nome                                                   | Descrição                                                           | Stakeholder | Requisito                   |
| ------------------------------------------------------ | ------------------------------------------------------------------- | ----------- | --------------------------- |
| [Procedure] sp_reservar_carro                          | Cria reserva e marca carro como reservado.                          | Funcionário | Evitar conflitos de reserva |
| [Procedure] sp_atualizar_reserva                       | Atualiza o estado (pendente/confirmada) ou datas de uma reserva.    | Funcionário | Gestão de estados           |
| [Procedure] sp_eliminar_reserva                        | Cancela e remove o registo de uma reserva, libertando o carro.      | Funcionário | Cancelamento de reserva     |
| [View] vw_reservas_detalhes (Simples)                  | Mostra reservas com cliente, carro e estado.                        | Funcionário | Acompanhamento operacional  |
| [Função] fn_reserva_disponivel (carro_id, inicio, fim) | Deteta conflitos de horário por carro.                              | Funcionário | Integridade de agenda       |
| [Trigger] tg_reservas_before_insert                    | Impede reserva se carro não disponível.                             | Funcionário | Consistência de reservas    |
| [Trigger] tg_reservas_after_delete                     | Volta a colocar o carro como disponível quando reserva é eliminada. | Funcionário | Libertação automática       |

---

## Tabela: vendas

**Responsável:** Guilherme

| Nome                                 | Descrição                                                                               | Stakeholder | Requisito                 |
| ------------------------------------ | --------------------------------------------------------------------------------------- | ----------- | ------------------------- |
| [Procedure] sp_registar_venda        | Valida carro, cria venda e marca carro como vendido (1 transação).                      | Funcionário | Atomicidade e integridade |
| [Procedure] sp_eliminar_venda        | Anula um registo de venda (revertendo o estado do carro para disponível, se aplicável). | Admin       | Correção de lançamentos   |
| [View] vw_vendas_completas (Simples) | Vendas com cliente, modelo do carro e preço final.                                      | Admin       | Relatório de vendas       |
| [Trigger] tg_vendas_before_insert    | Bloqueia se carro indisponível (vendido/reservado).                                     | Funcionário | Evitar dupla venda        |
| [Trigger] tg_vendas_after_delete     | Volta a colocar o carro como disponível quando a venda é eliminada.                     | Funcionário | Libertação automática     |

---

## Tabela: ordens_servico

**Responsável:** Tiago

| Nome                                                      | Descrição                                                                         | Stakeholder | Requisito             |
| --------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------- | --------------------- |
| [Procedure] sp_criar_os                                   | Abre ordem de serviço com cliente, carro, mecânico e tipo.                        | Funcionário | Fluxo de oficina      |
| [Procedure] sp_concluir_os                                | Marca OS como concluída e calcula valor total.                                    | Mecânico    | Finalização eficiente |
| [Procedure] sp_concluir_os                                | Elimina OS.                                                                       | Mecânico    |                       |
| [Função] fn_exportar_ordens_servico (inicio, fim, status) | Exporta ordens de serviço por período e status.                                   | Admin       | Exportação de dados   |
| [Trigger] tg_ordens_servico_status                        | Atualiza status automaticamente.                                                  | Admin       | Gestão de prazos      |
| [View] vw_os_em_andamento (Simples)                       | Lista todas as ordens de serviço que ainda não foram concluídas.                  | Funcionário | Dashboard operacional |
| [View] vw_os_atrasadas (Simples)                          | Lista ordens de serviço cuja data prevista já passou e calcula os dias de atraso. | Admin       | Controlo de prazos    |

---

## Tabela: avaliacoes

**Responsável:** Tiago

| Nome                                             | Descrição                                                                                   | Stakeholder      | Requisito                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- | ---------------- | -------------------------- |
| [Procedure] sp_inserir_avaliacao                 | Insere avaliação (cliente, carro/ordem_servico, comentário, rating, tipo).                  | Cliente          | Feedback do cliente        |
| [Procedure] sp_eliminar_avaliacao                | Remove um comentário ou classificação (por pedido do utilizador ou moderação).              | Admin            | Moderação de conteúdo      |
| [Procedure] sp_eliminar_avaliacao_por_utilizador | Permite que um utilizador (cliente ou mecânico) elimine apenas as suas próprias avaliações. | Cliente/Mecânico | Gestão de conteúdo próprio |
| [View] vw_avaliacoes_carros (Materializada)      | Mostra avaliações por carro com média.                                                      | Cliente          | Transparência na qualidade |
| [View] vw_avaliacoes_servicos (Materializada)    | Mostra avaliações de serviços de oficina.                                                   | Admin            | Qualidade dos serviços     |
| [View] vw_avaliacoes_detalhes (Simples)          | Lista avaliações com nome do cliente, info do carro e detalhes completos.                   | Funcionário      | Consulta detalhada         |

---

## B) MongoDB — Coleções

### Coleção: avaliacoes_detalhes

**Responsável:** Tiago

| Nome                          | Descrição                                                                                                              | Stakeholder | Requisito                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------- |
| [Coleção] avaliacoes_detalhes | Armazena comentários, fotos e resposta do stand para avaliações de clientes. Permite análise de sentimento e metadata. | Cliente     | Comentários flexíveis e metadata |

***

### Coleção: historico_manutencao

**Responsável:** Lucas

| Nome                           | Descrição                                                                                      | Stakeholder | Requisito                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------- |
| [Coleção] historico_manutencao | Registo técnico flexível de manutenções com lista de peças, diagnóstico e anexos (fotos/PDFs). | Funcionário | Histórico técnico flexível com documentos |

***

### Coleção: eventos_integracao

**Responsável:** Tiago

| Nome                         | Descrição                                                        | Stakeholder | Requisito            |
| ---------------------------- | ---------------------------------------------------------------- | ----------- | -------------------- |
| [Coleção] eventos_integracao | Outbox documental para reprocesso (eventos de sistemas externos) | Admin       | Integrações robustas |

***

### Coleção: diagnosticos_oficina

**Responsável:** Guilherme

| Nome                           | Descrição                                                                                  | Stakeholder | Requisito                     |
| ------------------------------ | ------------------------------------------------------------------------------------------ | ----------- | ----------------------------- |
| [Coleção] diagnosticos_oficina | Dados técnicos de scanner OBD-II com códigos de erro, parâmetros do motor e recomendações. | Mecânico    | Dados técnicos de scanner OBD |
