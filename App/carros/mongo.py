from django.conf import settings
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)

_client = None

def _redact_uri(uri: str | None) -> str:
    """Remove credenciais de uma URI antes de a escrever nos logs."""
    if not uri:
        return ''
    return re.sub(r'//([^:/@]+):[^@]+@', r'//\1:***@', uri)

def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not settings.MONGO_URI:
            logger.warning("[mongo] MONGO_URI não definido; a ligar ao default do driver (provavelmente localhost:27017)")
        if not getattr(settings, 'MONGO_DB_NAME', None) or settings.MONGO_DB_NAME == 'mongo_db':
            logger.warning("[mongo] A usar MONGO_DB_NAME='%s' (default). Defina MONGO_DB_NAME no .env para evitar escrever na BD errada.", settings.MONGO_DB_NAME)
        logger.info("[mongo] A ligar a URI=%s | DB=%s", _redact_uri(settings.MONGO_URI), settings.MONGO_DB_NAME)
        _client = MongoClient(settings.MONGO_URI)
        try:
            _client.admin.command('ping')
            logger.info("[mongo] Ping OK")
        except Exception as e:
            logger.error("[mongo] Falha no ping ao servidor Mongo: %s", e)
    return _client

def get_db():
    return get_client()[settings.MONGO_DB_NAME]

# Coleções MongoDB
_historico_manutencao_col = None
def historico_manutencao_col():
    global _historico_manutencao_col
    if _historico_manutencao_col is None:
        col_name = getattr(settings, 'MONGO_HISTORICO_MANUTENCAO_COLLECTION', 'historico_manutencao')
        logger.info("[mongo] Coleção histórico manutenção: %s (DB=%s)", col_name, settings.MONGO_DB_NAME)
        _historico_manutencao_col = get_db()[col_name]
    return _historico_manutencao_col

_diagnosticos_oficina_col = None
def diagnosticos_oficina_col():
    global _diagnosticos_oficina_col
    if _diagnosticos_oficina_col is None:
        col_name = getattr(settings, 'MONGO_DIAGNOSTICOS_OFICINA_COLLECTION', 'diagnosticos_oficina')
        logger.info("[mongo] Coleção diagnósticos oficina: %s (DB=%s)", col_name, settings.MONGO_DB_NAME)
        _diagnosticos_oficina_col = get_db()[col_name]
    return _diagnosticos_oficina_col

_avaliacoes_detalhes_col = None
def avaliacoes_detalhes_col():
    global _avaliacoes_detalhes_col
    if _avaliacoes_detalhes_col is None:
        col_name = getattr(settings, 'MONGO_AVALIACOES_DETALHES_COLLECTION', 'avaliacoes_detalhes')
        logger.info("[mongo] Coleção avaliações detalhes: %s (DB=%s)", col_name, settings.MONGO_DB_NAME)
        _avaliacoes_detalhes_col = get_db()[col_name]
    return _avaliacoes_detalhes_col

_eventos_integracao_col = None
def eventos_integracao_col():
    global _eventos_integracao_col
    if _eventos_integracao_col is None:
        col_name = getattr(settings, 'MONGO_EVENTOS_INTEGRACAO_COLLECTION', 'eventos_integracao')
        logger.info("[mongo] Coleção eventos integração: %s (DB=%s)", col_name, settings.MONGO_DB_NAME)
        _eventos_integracao_col = get_db()[col_name]
    return _eventos_integracao_col

def oid(value: str | None) -> ObjectId | None:
    """Try to convert a string to ObjectId; return None if invalid/empty."""
    if not value:
        return None
    try:
        return ObjectId(value)
    except Exception:
        return None

def to_json(doc):
    """Serialize a BSON document (or list) to a Python dict/list safe for JSONResponse."""
    import json
    return json.loads(dumps(doc))


# Classes para trabalhar com as coleções MongoDB

class HistoricoManutencao:
    """Classe para gerenciar histórico de manutenção dos veículos"""

    @staticmethod
    def inserir_registro(carro_id: int, ordem_servico_id: int, descricao: str,
                        mecanico: Dict, pecas_utilizadas: List[Dict],
                        diagnostico: Dict, custo_total: float,
                        tempo_execucao_minutos: int,
                        proxima_revisao_km: Optional[int] = None,
                        anexos: Optional[List[Dict]] = None) -> str:
        """Insere um novo registro de manutenção"""
        documento = {
            "carro_id": carro_id,
            "ordem_servico_id": ordem_servico_id,
            "descricao": descricao,
            "data": datetime.now(timezone.utc),
            "mecanico": mecanico,
            "pecas_utilizadas": pecas_utilizadas,
            "diagnostico": diagnostico,
            "anexos": anexos or [],
            "custo_total": custo_total,
            "tempo_execucao_minutos": tempo_execucao_minutos,
            "proxima_revisao_km": proxima_revisao_km,
            "created_at": datetime.now(timezone.utc)
        }

        result = historico_manutencao_col().insert_one(documento)
        return str(result.inserted_id)

    @staticmethod
    def buscar_por_carro(carro_id: int) -> List[Dict]:
        """Busca histórico de manutenção por ID do carro"""
        return list(historico_manutencao_col().find({"carro_id": carro_id}).sort("data", -1))

    @staticmethod
    def buscar_por_ordem_servico(ordem_servico_id: int) -> Optional[Dict]:
        """Busca registro de manutenção por ID da ordem de serviço"""
        return historico_manutencao_col().find_one({"ordem_servico_id": ordem_servico_id})

    @staticmethod
    def eliminar_por_id(doc_id: str) -> bool:
        """Elimina um documento de histórico de manutenção pelo _id (string)."""
        oid_val = oid(doc_id)
        if not oid_val:
            return False
        result = historico_manutencao_col().delete_one({'_id': oid_val})
        return result.deleted_count > 0


class DiagnosticosOficina:
    """Classe para gerenciar diagnósticos da oficina"""

    @staticmethod
    def inserir_diagnostico(ordem_servico_id: int, carro_id: int,
                           scanner_data: Dict, codigos_erro: List[Dict],
                           recomendacoes: List[Dict], mecanico: Dict,
                           duracao_diagnostico_minutos: int) -> str:
        """Insere um novo diagnóstico"""
        documento = {
            "ordem_servico_id": ordem_servico_id,
            "carro_id": carro_id,
            "scanner_data": scanner_data,
            "codigos_erro": codigos_erro,
            "recomendacoes": recomendacoes,
            "mecanico": mecanico,
            "timestamp": datetime.now(timezone.utc),
            "duracao_diagnostico_minutos": duracao_diagnostico_minutos
        }

        result = diagnosticos_oficina_col().insert_one(documento)
        return str(result.inserted_id)

    @staticmethod
    def buscar_por_ordem_servico(ordem_servico_id: int) -> Optional[Dict]:
        """Busca diagnóstico por ID da ordem de serviço"""
        return diagnosticos_oficina_col().find_one({"ordem_servico_id": ordem_servico_id})

    @staticmethod
    def buscar_por_carro(carro_id: int) -> List[Dict]:
        """Busca diagnósticos por ID do carro"""
        return list(diagnosticos_oficina_col().find({"carro_id": carro_id}).sort("timestamp", -1))

    @staticmethod
    def eliminar_por_id(doc_id: str) -> bool:
        """Elimina um documento de diagnóstico pelo _id (string)."""
        oid_val = oid(doc_id)
        if not oid_val:
            return False
        result = diagnosticos_oficina_col().delete_one({'_id': oid_val})
        return result.deleted_count > 0


class AvaliacoesDetalhes:
    """Classe para gerenciar detalhes das avaliações"""

    @staticmethod
    def inserir(avaliacao_data: Dict) -> Optional[str]:
        """Insere uma nova avaliação detalhada"""
        documento = {
            **avaliacao_data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        try:
            result = avaliacoes_detalhes_col().insert_one(documento)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir avaliação: {e}")
            return None

    @staticmethod
    def inserir_avaliacao_detalhada(avaliacao_id: int, comentario: str,
                                   fotos: Optional[List[str]] = None,
                                   resposta_stand: Optional[Dict] = None,
                                   metadata: Optional[Dict] = None) -> str:
        """Insere detalhes de uma avaliação"""
        documento = {
            "avaliacao_id": avaliacao_id,
            "comentario": comentario,
            "fotos": fotos or [],
            "resposta_stand": resposta_stand,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        result = avaliacoes_detalhes_col().insert_one(documento)
        return str(result.inserted_id)

    @staticmethod
    def buscar_por_avaliacao(avaliacao_id: int) -> Optional[Dict]:
        """Busca detalhes por ID da avaliação"""
        return avaliacoes_detalhes_col().find_one({"avaliacao_id": avaliacao_id})

    @staticmethod
    def eliminar_por_id(doc_id: str) -> bool:
        """Elimina um documento de avaliação detalhada pelo _id (string)."""
        oid_val = oid(doc_id)
        if not oid_val:
            return False
        result = avaliacoes_detalhes_col().delete_one({'_id': oid_val})
        return result.deleted_count > 0

    @staticmethod
    def eliminar_por_avaliacao_id(avaliacao_id: int) -> int:
        """Elimina todos os detalhes associados a uma avaliação (por avaliacao_id). Retorna número de removidos."""
        result = avaliacoes_detalhes_col().delete_many({'avaliacao_id': int(avaliacao_id)})
        return result.deleted_count

    @staticmethod
    def atualizar_resposta(avaliacao_id: int, resposta_texto: str, respondido_por: str) -> bool:
        """Atualiza a resposta do stand para uma avaliação"""
        resposta = {
            "texto": resposta_texto,
            "data": datetime.now(timezone.utc),
            "respondido_por": respondido_por
        }

        result = avaliacoes_detalhes_col().update_one(
            {"avaliacao_id": avaliacao_id},
            {
                "$set": {
                    "resposta_stand": resposta,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count > 0


class EventosIntegracao:
    """Classe para gerenciar eventos de integração entre sistemas"""

    @staticmethod
    def criar_evento(tipo: str, payload: Dict, destinos: List[Dict],
                    max_retries: int = 3) -> str:
        """Cria um novo evento de integração"""
        evento_id = f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:-3]}{str(payload.get('venda_id', '000')).zfill(3)}"

        documento = {
            "evento_id": evento_id,
            "tipo": tipo,
            "payload": payload,
            "status": "pendente",
            "retry_count": 0,
            "max_retries": max_retries,
            "proxima_tentativa": None,
            "destinos": destinos,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        result = eventos_integracao_col().insert_one(documento)
        return evento_id

    @staticmethod
    def atualizar_status_evento(evento_id: str, status: str,
                               destino_index: int, http_status: int,
                               response_body: Dict, tempo_resposta_ms: int) -> bool:
        """Atualiza o status de processamento de um destino específico"""
        result = eventos_integracao_col().update_one(
            {"evento_id": evento_id},
            {
                "$set": {
                    f"destinos.{destino_index}.status": "sucesso" if http_status < 400 else "falha",
                    f"destinos.{destino_index}.http_status": http_status,
                    f"destinos.{destino_index}.response_body": response_body,
                    f"destinos.{destino_index}.processado_em": datetime.now(timezone.utc),
                    f"destinos.{destino_index}.tempo_resposta_ms": tempo_resposta_ms,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count > 0

    @staticmethod
    def buscar_eventos_pendentes() -> List[Dict]:
        """Busca eventos pendentes para processamento"""
        return list(eventos_integracao_col().find({"status": "pendente"}))

    @staticmethod
    def incrementar_retry_count(evento_id: str) -> bool:
        """Incrementa contador de tentativas de um evento"""
        result = eventos_integracao_col().update_one(
            {"evento_id": evento_id},
            {
                "$inc": {"retry_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        return result.modified_count > 0

    @staticmethod
    def eliminar_evento(evento_id: str) -> bool:
        """Elimina um evento de integração pelo seu campo evento_id."""
        if not evento_id:
            return False
        result = eventos_integracao_col().delete_one({'evento_id': evento_id})
        return result.deleted_count > 0

    @staticmethod
    def set_status(evento_id: str, status: str) -> bool:
        """Define o status do evento (ex: 'pendente' ou 'processado')."""
        if not evento_id:
            return False
        result = eventos_integracao_col().update_one(
            {'evento_id': evento_id},
            {'$set': {'status': status, 'updated_at': datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0

    @staticmethod
    def set_destino_status(evento_id: str, destino_index: int, status: str, http_status: int | None = None, response_body: Dict | None = None) -> bool:
        """Atualiza o status de um destino específico (por índice) dentro do documento do evento."""
        if not evento_id:
            return False
        update_fields = {
            f'destinos.{destino_index}.status': status,
            'updated_at': datetime.now(timezone.utc)
        }
        if http_status is not None:
            update_fields[f'destinos.{destino_index}.http_status'] = http_status
        if response_body is not None:
            update_fields[f'destinos.{destino_index}.response_body'] = response_body
            update_fields[f'destinos.{destino_index}.processado_em'] = datetime.now(timezone.utc)
        result = eventos_integracao_col().update_one({'evento_id': evento_id}, {'$set': update_fields})
        return result.modified_count > 0