import math
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver
from app.models import alert as models_alert
from app.models import reservoir as models_reservoir
from app.schemas import alerts as schemas_alerts
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.models import user as models_user
from app.core.database import commit_or_rollback, get_background_db_session
from app.services import graph as services_graph
from app.core.config import settings
from app.utils.logger_config import setup_logger
from app.utils.retriever import ensemble_retrieve
import json
from langchain_core.prompts import PromptTemplate
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

logger = setup_logger(__name__)


async def get_alert_detail(
    db: AsyncSession,
    alert_id: int,
):
    """获取预警详情"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)

    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    return schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)


async def get_alert_trace(
    db: AsyncSession,
    neo4j_driver: AsyncDriver,
    alert_id: int,
):
    """获取预警溯源路径"""
    alert = await db.get(models_alert.AlertEvent, alert_id)
    if not alert:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    reservoir = await db.get(models_reservoir.Reservoir, alert.reservoir_id)
    if not reservoir:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "关联水库不存在")

    result = await services_graph.trace_pollution(neo4j_driver, reservoir.code)
    return schemas_alerts.GetTracePollutionResponse(**result.model_dump())


async def get_alert_list(
    db: AsyncSession,
    request: schemas_alerts.GetAlertListRequest,
):
    """获取预警列表"""

    stmt = select(models_alert.AlertEvent, models_user.User.real_name).outerjoin(
        models_user.User, models_alert.AlertEvent.handler_id == models_user.User.id
    )
    if request.reservoir_id is not None:
        stmt = stmt.where(models_alert.AlertEvent.reservoir_id == request.reservoir_id)
    if request.alert_level is not None:
        stmt = stmt.where(models_alert.AlertEvent.alert_level == request.alert_level)
    if request.status is not None:
        stmt = stmt.where(models_alert.AlertEvent.status == request.status)
    if request.source is not None:
        stmt = stmt.where(models_alert.AlertEvent.source == request.source)
    if request.start_time is not None:
        stmt = stmt.where(models_alert.AlertEvent.detected_at >= request.start_time)
    if request.end_time is not None:
        stmt = stmt.where(models_alert.AlertEvent.detected_at <= request.end_time)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    alert_entity_list = (
        await db.execute(
            stmt.order_by(models_alert.AlertEvent.detected_at.desc())
            .offset((request.page - 1) * request.page_size)
            .limit(request.page_size)
        )
    ).all()

    result_list: list[schemas_alerts.GetAlertListResponse] = []
    for alert_event, handler_name in alert_entity_list:
        resp = schemas_alerts.GetAlertListResponse.model_validate(alert_event)
        resp.handler_name = handler_name
        result_list.append(resp)

    return PaginatedResponse(
        lists=result_list,
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total,
            total_pages=math.ceil(total / request.page_size),
        ),
    )


async def update_alert(
    db: AsyncSession,
    alert_id: int,
    update_alert_request: schemas_alerts.UpdateAlertRequest,
):
    """更新预警状态"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)

    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    alert_entity.status = update_alert_request.status
    alert_entity.handler_id = update_alert_request.handler_id

    await commit_or_rollback(db)
    return schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)


async def add_alert_note(
    db: AsyncSession,
    alert_id: int,
    user_id: int,
    request: schemas_alerts.AddAlertNoteRequest,
):
    """添加处置备注"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)
    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    current_notes = list(alert_entity.notes or [])
    new_id = max((n.get("id", 0) for n in current_notes), default=0) + 1
    now = datetime.now()

    new_note = {
        "id": new_id,
        "user_id": user_id,
        "content": request.content,
        "created_at": now.isoformat(),
    }
    current_notes.append(new_note)
    alert_entity.notes = current_notes

    await commit_or_rollback(db)
    return schemas_alerts.AlertNoteResponse(**new_note)


async def get_unread_alert_count(db: AsyncSession):
    """获取未读预警数"""
    count = await db.scalar(
        select(func.count(models_alert.AlertEvent.id)).where(
            models_alert.AlertEvent.status == 0
        )
    )
    return schemas_alerts.GetUnreadCountResponse(count=count or 0)


async def batch_read_alerts(
    db: AsyncSession, request: schemas_alerts.BatchReadAlertsRequest
):
    """批量标记已读"""
    stmt = select(models_alert.AlertEvent).where(
        models_alert.AlertEvent.id.in_(request.ids)
    )
    alert_entities = (await db.execute(stmt)).scalars().all()

    for entity in alert_entities:
        entity.status = 1
        if request.handler_id is not None:
            entity.handler_id = request.handler_id

    await commit_or_rollback(db)
    return True


async def confirm_suggestion(db: AsyncSession, alert_id: int):
    """确认 AI 处置建议"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)
    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")
    status_labels = {0: "未生成", 1: "生成中", 2: "已生成", 3: "已确认"}
    current = status_labels.get(alert_entity.suggestion_status, "未知")
    if alert_entity.suggestion_status != 2:
        raise ServiceException(
            ErrorCode.BUSINESS_ERROR,
            f"建议状态不允许确认（当前：{current}）",
        )
    alert_entity.suggestion_status = 3
    await commit_or_rollback(db)
    return schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)


async def llm_suggestion(alert_id: int):
    """为指定预警生成 AI 处置建议（自建 DB/Neo4j session）"""
    from app.core.neo4j import driver as neo4j_driver

    async with get_background_db_session() as db:
        alert_entity = await db.get(models_alert.AlertEvent, alert_id)
        if not alert_entity:
            logger.warning(f"预警不存在，跳过建议生成: alert_id={alert_id}")
            return

        if alert_entity.suggestion_status == 1:
            logger.info(f"建议生成中，跳过重复触发: alert_id={alert_id}")
            return

        alert_entity.suggestion_status = 1
        await commit_or_rollback(db)

    async with get_background_db_session() as db:
        try:
            alert_entity = await db.get(models_alert.AlertEvent, alert_id)
            if not alert_entity:
                logger.warning(f"预警不存在, alert_id={alert_id}")
                return

            reservoir_entity = await db.get(
                models_reservoir.Reservoir, alert_entity.reservoir_id
            )
            if not reservoir_entity:
                logger.warning(f"水库不存在, alert_id={alert_id}")
                return

            async with neo4j_driver.session() as neo4j_session:
                source_desc = json.dumps(
                    (
                        await services_graph.trace_pollution(neo4j_session, reservoir_entity.code)
                    ).model_dump()
                )

            query = (
                " ".join(
                    [ind.get("name", "") for ind in alert_entity.indicators if ind.get("name")]
                )
                + " 超标 处置 应急 水质标准"
            )
            rag_doc_list = await ensemble_retrieve(query, top_k=10)
            rag_content_section = ""
            for index, doc in enumerate(rag_doc_list):
                rag_content_section += f"第{index}个文档内容：\n{doc.page_content}\n"

            suggestion_input = schemas_alerts.SuggestionPromptInputItem(
                reservoir_name=reservoir_entity.name,
                reservoir_code=reservoir_entity.code,
                reservoir_location=reservoir_entity.location,
                watershed=reservoir_entity.watershed,
                capacity=reservoir_entity.capacity,
                water_grade=reservoir_entity.water_grade,
                alert_level=alert_entity.alert_level,
                detected_at=alert_entity.detected_at,
                source_desc=source_desc,
                indicators_text=json.dumps(alert_entity.indicators),
                rag_content_section=rag_content_section,
            )

            system_prompt = PromptTemplate.from_template(
                get_prompt.alert["SUGGESTION"]["SYSTEM"]
            ).format()
            user_prompt = PromptTemplate.from_template(
                get_prompt.alert["SUGGESTION"]["USER"]
            ).format(**suggestion_input.model_dump())
            llm_messages = [(SystemMessage(system_prompt)), (HumanMessage(user_prompt))]

            model = get_model.build_chat_model(thinking=False)

            chain = model | JsonOutputParser()
            json_output: list[dict] = await chain.ainvoke(llm_messages)

            logger.info(f"ai生成建议完成, alert_id={alert_id}")

            alert_entity.suggestion = json_output
            alert_entity.suggestion_status = 2
            await commit_or_rollback(db)
        except Exception:
            if alert_entity:
                alert_entity.suggestion_status = 0
                await commit_or_rollback(db)
            logger.error(f"建议生成异常: alert_id={alert_id}", exc_info=True)


async def get_similar_events(
    db: AsyncSession,
    alert_id: int,
    page: int = 1,
    page_size: int = 10,
):
    """获取历史相似事件（同水库、按指标匹配数排序）"""
    alert = await db.get(models_alert.AlertEvent, alert_id)
    if not alert:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    current_indicator_names = {
        ind.get("name") for ind in (alert.indicators or []) if ind.get("name")
    }
    three_years_ago = datetime.now().replace(year=datetime.now().year - 3)

    stmt = (
        select(models_alert.AlertEvent)
        .where(
            models_alert.AlertEvent.reservoir_id == alert.reservoir_id,
            models_alert.AlertEvent.status == 3,
            models_alert.AlertEvent.id != alert_id,
            models_alert.AlertEvent.detected_at >= three_years_ago,
        )
        .order_by(models_alert.AlertEvent.detected_at.desc())
    )
    all_candidates = (await db.execute(stmt)).scalars().all()

    scored = []
    for candidate in all_candidates:
        candidate_names = {
            ind.get("name") for ind in (candidate.indicators or []) if ind.get("name")
        }
        match_count = len(current_indicator_names & candidate_names)
        scored.append((candidate, match_count))

    scored.sort(key=lambda x: (x[1], x[0].detected_at), reverse=True)

    total = len(scored)
    offset = (page - 1) * page_size
    page_items = scored[offset : offset + page_size]

    result_list = []
    for candidate, match_count in page_items:
        item = schemas_alerts.SimilarEventItem.model_validate(candidate)
        item.matched_indicators = list(
            current_indicator_names
            & {
                ind.get("name")
                for ind in (candidate.indicators or [])
                if ind.get("name")
            }
        )
        result_list.append(item)

    return PaginatedResponse(
        lists=result_list,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        ),
    )
