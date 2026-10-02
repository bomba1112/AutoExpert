# ruff: noqa: E501

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.core.abbreviations import EXPLANATIONS, AbbreviationExplainer
from app.models.enums import ChatRole, DataOrigin, EvidenceStatus
from app.schemas.chat import ChatContextSnapshot, ChatConversationTurn, GroundedChatDraft

_INSUFFICIENT = {
    "ru": "По имеющимся источникам недостаточно данных, чтобы уверенно это утверждать.",
    "az": "Mövcud mənbələrə əsasən bunu əminliklə demək üçün məlumat kifayət deyil.",
    "en": "The available sources do not contain enough evidence to state that confidently.",
}

_INSPECTION = {
    "ru": "Состояние конкретного экземпляра требует физической проверки.",
    "az": "Konkret avtomobilin vəziyyəti fiziki yoxlama tələb edir.",
    "en": "The condition of the specific vehicle requires a physical inspection.",
}


class DeterministicGroundedChatProvider:
    """Development LLM adapter that can only compose facts from ChatContextSnapshot."""

    name = "deterministic_grounded_chat"

    def answer_chat(
        self,
        *,
        context: ChatContextSnapshot,
        conversation: list[ChatConversationTurn],
        question: str,
    ) -> GroundedChatDraft:
        language = context.language
        normalized = question.casefold()
        glossary = self._glossary(language, conversation)
        mileage = self._remembered_mileage(question, conversation)

        if self._contains(
            normalized,
            (
                "скрыт",
                "внутренний json",
                "backend payload",
                "system prompt",
                "ignore previous",
                "hidden data",
                "gizli məlumat",
                "tam json",
            ),
        ):
            return self._payload_refusal(context, language, glossary)

        if self._contains(normalized, ("airbag", "подуш", "hava yast")):
            return self._airbag_answer(language)

        if not context.is_demo:
            intent = None
            if self._contains(
                normalized,
                ("именно к моей", "моей версии", "my version", "my variant", "mənim versiyama"),
            ):
                intent = "variant_applicability"
            elif self._contains(
                normalized, ("почему показана", "why is this recall", "niyə bu geri")
            ):
                intent = "variant_recall"
            elif self._contains(
                normalized,
                ("лошадиных", "мощност", "horsepower", "system power", "at gücü", "gücü"),
            ):
                intent = "variant_power"
            elif self._contains(
                normalized, ("это гибрид", "is it a hybrid", "is this a hybrid", "bu hibrid")
            ):
                intent = "variant_identity"
            if intent:
                section = self._find_section(context, intent)
                if section and section.claims:
                    draft = self._draft_from_section(
                        section, "\n\n".join(c.text for c in section.claims)
                    )
                    if any(c.status == EvidenceStatus.INSUFFICIENT_DATA for c in section.claims):
                        draft.status = EvidenceStatus.INSUFFICIENT_DATA
                    return draft
                return self._insufficient(language)
            if self._contains(normalized, ("фото", "photo", "şəkil", "sekil")):
                return self._section_answer(context, language, "vin_photos", glossary)
            if self._contains(normalized, ("аукцион", "auction", "hərrac", "herrac")):
                return self._section_answer(context, language, "vin_auction", glossary)
            if self._contains(
                normalized,
                (
                    "какой был пробег",
                    "пробег на аукцион",
                    "recorded mileage",
                    "what was the mileage",
                    "əvvəlki yürüş",
                    "yürüş nə qədər idi",
                ),
            ):
                return self._section_answer(context, language, "vin_mileage", glossary)
            if self._contains(
                normalized,
                (
                    "владельц",
                    "отдельные жалобы",
                    "частая проблема",
                    "owner",
                    "anecdote",
                    "common problem",
                    "sahiblər",
                    "sahibler",
                    "ayrı şikayət",
                    "tez-tez",
                ),
            ):
                section = self._find_section(context, "owner_reviews")
                if section and section.claims:
                    text = "\n\n".join(c.text for c in section.claims[:10])
                    result = self._draft_from_section(section, text)
                    # Owner self-reports never establish population reliability.
                    result.status = EvidenceStatus.INSUFFICIENT_DATA
                    return result
                return self._insufficient(language)

        if self._contains(normalized, ("salvage", "тотал", "утилиз", "xilasetmə")):
            return self._salvage_answer(context, language, glossary)

        if self._contains(
            normalized, ("объявлен", "продав", "listing", "seller", "elan", "satıcı")
        ):
            section = self._find_section(context, "offer")
            if section:
                label = {
                    "ru": "Указано продавцом, независимо не подтверждено:",
                    "az": "Satıcının məlumatı, müstəqil təsdiqlənməyib:",
                    "en": "Seller claims, not independently verified:",
                }[language]
                return self._draft_from_section(section, label + "\n" + self._section_text(section))

        if self._contains(
            normalized, ("бензин", "топлив", "gasoline", "fuel", "benzin", "yanacaq")
        ):
            section = self._find_section(context, "engine")
            if section:
                claims = [
                    c
                    for c in section.claims
                    if self._contains(
                        c.text.casefold(),
                        (
                            "бензин",
                            "топлив",
                            "октан",
                            "gasoline",
                            "fuel",
                            "octane",
                            "benzin",
                            "yanacaq",
                            "oktan",
                        ),
                    )
                ]
                if claims:
                    return self._draft_from_section(
                        section.model_copy(update={"claims": claims}),
                        "\n".join(c.text for c in claims),
                    )
            return self._insufficient(language)

        if self._contains(
            normalized,
            ("recall", "отзывн", "кампан", "geri çağır", "geri cagir", "tsb"),
        ):
            return self._section_answer(context, language, "recalls_tsb", glossary)

        if self._contains(
            normalized,
            ("откуда", "источник", "source", "mənbə", "menbe"),
        ):
            return self._sources_answer(context, language)

        if self._contains(
            normalized,
            ("цен", "27 500", "27500", "price", "qiymət", "торг", "bargain", "endirim"),
        ):
            return self._price_answer(context, question, language)

        if self._contains(
            normalized,
            ("менял короб", "заменил короб", "replaced transmission", "qutunu dəyiş"),
        ):
            return self._replacement_followup(language, mileage)

        if self._contains(
            normalized,
            ("короб", "акпп", "8at", "transmission", "sürətlər qut", "suretler qut"),
        ):
            return self._transmission_answer(context, language, glossary, mileage)

        if self._contains(
            normalized,
            ("двигател", "мотор", "engine", "mühərrik", "muherrik", "a25a"),
        ):
            return self._engine_answer(context, language, glossary)

        if self._contains(normalized, ("дорог", "expensive", "bahalı", "bahali")):
            return self._expensive_issue_answer(context, language)

        if self._contains(normalized, ("слаб", "weak", "zəif")):
            return self._weak_points_answer(context, language)

        if self._contains(
            normalized,
            ("перед покуп", "before purchase", "almazdan əvvəl", "almazdan evvel"),
        ):
            return self._section_answer(context, language, "pre_purchase_check", glossary)

        if self._contains(
            normalized,
            ("спросить продав", "что спрос", "ask the seller", "satıcıdan", "saticidan"),
        ):
            return self._seller_answer(context, language)

        if self._contains(
            normalized,
            ("плохих дорог", "плохие дороги", "poor roads", "pis yol", "bərbad yol"),
        ):
            return self._poor_roads_answer(language)

        if mileage is not None or self._contains(
            normalized,
            ("пробег", "что проверить", "mileage", "what to inspect", "yürüş", "nəyi yoxla"),
        ):
            return self._mileage_answer(context, language, mileage)

        return self._insufficient(language)

    def _payload_refusal(
        self,
        context: ChatContextSnapshot,
        language: str,
        glossary: AbbreviationExplainer,
    ) -> GroundedChatDraft:
        vin = glossary.render("VIN")
        if not context.vin_summary.history_unlocked:
            text = {
                "ru": f"Коротко: закрытые данные не раскрываются через чат. История {vin} не разблокирована, поэтому её деталей нет в контексте Auto Expert.",
                "az": f"Qısa cavab: bağlı məlumatlar çat vasitəsilə açıqlanmır. {vin} tarixçəsi açılmayıb və detalları Auto Expert kontekstində yoxdur.",
                "en": f"Short answer: chat cannot reveal locked data. The {vin} history is not unlocked, so those details are absent from Auto Expert context.",
            }[language]
        else:
            text = {
                "ru": "Коротко: внутренний JSON и служебные данные я не показываю. Могу объяснить конкретную запись из уже разблокированного отчёта.",
                "az": "Qısa cavab: daxili JSON və xidmət məlumatlarını göstərmirəm. Açılmış hesabatdakı konkret qeydi izah edə bilərəm.",
                "en": "Short answer: I do not expose internal JSON or service data. I can explain a specific record from the unlocked report.",
            }[language]
        return GroundedChatDraft(text=text, status=EvidenceStatus.INSUFFICIENT_DATA)

    def _salvage_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
        glossary: AbbreviationExplainer,
    ) -> GroundedChatDraft:
        if not context.vin_summary.has_salvage_title:
            return self._insufficient(language)
        vin = glossary.render("VIN")
        text = {
            "ru": f"Коротко: это серьёзный повод для осторожности, но не автоматический отказ. В доступном тестовом отчёте {vin} отмечен Salvage; эта запись не подтверждает качество восстановления конкретной машины. Действие: {_INSPECTION['ru']}",
            "az": f"Qısa cavab: bu, ciddi ehtiyat siqnalıdır, amma avtomatik imtina demək deyil. Mövcud DEMO {vin} hesabatında Salvage qeyd olunub; bu qeyd konkret avtomobilin təmir keyfiyyətini təsdiqləmir. Addım: {_INSPECTION['az']}",
            "en": f"Short answer: this is a serious caution flag, not an automatic rejection. The available DEMO {vin} snapshot marks Salvage; that record does not confirm the repair quality of this specific car. Action: {_INSPECTION['en']}",
        }[language]
        return GroundedChatDraft(
            text=text,
            status=EvidenceStatus.ESTIMATE,
            source_ids=self._sources_for_origin(context, DataOrigin.DEMO)[:1],
            evidence_ids=["vin_summary.salvage"],
        )

    def _airbag_answer(self, language: str) -> GroundedChatDraft:
        text = {
            "ru": f"Коротко: слов продавца недостаточно. В доступном контексте нет подтверждения восстановления подушек безопасности. По VIN это подтвердить нельзя — нужен физический осмотр. Действие: {_INSPECTION['ru']}",
            "az": f"Qısa cavab: satıcının sözü kifayət deyil. Mövcud kontekstdə hava yastıqlarının bərpasını təsdiqləyən məlumat yoxdur. Bunu VIN ilə təsdiqləmək olmur — fiziki baxış lazımdır. Addım: {_INSPECTION['az']}",
            "en": f"Short answer: the seller's statement is not enough. The available context does not confirm that the airbags were restored. VIN data cannot confirm this — a physical inspection is required. Action: {_INSPECTION['en']}",
        }[language]
        return GroundedChatDraft(text=text, status=EvidenceStatus.NEEDS_INSPECTION)

    def _price_answer(
        self,
        context: ChatContextSnapshot,
        question: str,
        language: str,
    ) -> GroundedChatDraft:
        market = context.market_analysis
        if market.status == EvidenceStatus.INSUFFICIENT_DATA or market.median is None:
            return self._insufficient(
                language,
                detail={
                    "ru": "В отчёте нет достаточной выборки сопоставимых местных объявлений, поэтому цену автомобиля я не придумываю.",
                    "az": "Snapshot-da kifayət qədər müqayisə edilən yerli elan yoxdur, buna görə avtomobil qiyməti uydurulmur.",
                    "en": "The snapshot has no sufficient local comparable sample, so I will not invent a vehicle price.",
                }[language],
            )
        asked_price = self._money_value(question)
        comparison = ""
        if asked_price is not None:
            deviation = (asked_price - market.median) / market.median * Decimal(100)
            comparison = {
                "ru": f" Указанная цена отличается от медианы примерно на {deviation.quantize(Decimal('0.1'))}%.",
                "az": f" Göstərilən qiymət mediandan təxminən {deviation.quantize(Decimal('0.1'))}% fərqlənir.",
                "en": f" The stated price differs from the median by about {deviation.quantize(Decimal('0.1'))}%.",
            }[language]
        text = {
            "ru": f"Коротко: ориентир отчёта — медиана {market.median} {market.currency}.{comparison} Это оценка цен объявлений, не подтверждённая цена сделки.",
            "az": f"Qısa cavab: hesabat üzrə median {market.median} {market.currency}-dir.{comparison} Bu, elan qiymətlərinin təxminidir, təsdiqlənmiş satış qiyməti deyil.",
            "en": f"Short answer: the snapshot median is {market.median} {market.currency}.{comparison} This is an asking-price estimate, not a confirmed transaction price.",
        }[language]
        return GroundedChatDraft(
            text=text,
            status=market.status,
            source_ids=market.source_ids,
            evidence_ids=["market_analysis"],
        )

    def _replacement_followup(self, language: str, mileage: int | None) -> GroundedChatDraft:
        remembered = self._mileage_phrase(language, mileage)
        text = {
            "ru": f"Коротко: замена коробки сама по себе не доказывает её текущее состояние.{remembered} В доступных источниках нет данных о конкретной установленной коробке и качестве работ. {_INSUFFICIENT['ru']} Действие: {_INSPECTION['ru']}",
            "az": f"Qısa cavab: sürətlər qutusunun dəyişdirilməsi onun indiki vəziyyətini özü-özlüyündə sübut etmir.{remembered} Mövcud mənbələrdə quraşdırılmış qutu və işin keyfiyyəti barədə məlumat yoxdur. {_INSUFFICIENT['az']} Addım: {_INSPECTION['az']}",
            "en": f"Short answer: a replaced transmission does not by itself prove its current condition.{remembered} The available sources do not identify the installed unit or the quality of the work. {_INSUFFICIENT['en']} Action: {_INSPECTION['en']}",
        }[language]
        return GroundedChatDraft(text=text, status=EvidenceStatus.NEEDS_INSPECTION)

    def _transmission_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
        glossary: AbbreviationExplainer,
        mileage: int | None,
    ) -> GroundedChatDraft:
        transmission = context.vehicle_profile.transmission or "—"
        term = glossary.render(transmission)
        remembered = self._mileage_phrase(language, mileage)
        section = self._find_section(context, "transmission")
        if (
            context.vehicle_profile.data_origin == DataOrigin.REAL
            and section
            and any(item.status == EvidenceStatus.CONFIRMED for item in section.claims)
        ):
            claims = self._section_text(section)
            text = {
                "ru": f"По данным досье: {claims} Подтверждённой оценки ресурса или вероятности поломки в источниках нет.{remembered}",
                "az": f"Dosyeyə əsasən: {claims} Mənbələrdə təsdiqlənmiş resurs və ya nasazlıq ehtimalı yoxdur.{remembered}",
                "en": f"According to the dossier: {claims} The sources do not provide a confirmed lifespan or failure probability.{remembered}",
            }[language]
            return self._draft_from_section(section, text)
        detail = {
            "ru": f"Профиль определяет коробку как {term}, но отчёте не содержит подтверждённой оценки её ресурса или вероятности поломки.{remembered}",
            "az": f"Profil sürətlər qutusunu {term} kimi müəyyən edir, amma hesabatda onun resursu və ya nasazlıq ehtimalı barədə təsdiqlənmiş qiymətləndirmə yoxdur.{remembered}",
            "en": f"The profile identifies the transmission as {term}, but the snapshot has no confirmed lifespan or failure-probability assessment.{remembered}",
        }[language]
        claim = self._first_claim(context, "transmission")
        return self._insufficient(
            language,
            detail=detail,
            source_ids=claim.source_ids if claim else [],
            evidence_ids=claim.evidence_ids if claim else [],
        )

    def _engine_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
        glossary: AbbreviationExplainer,
    ) -> GroundedChatDraft:
        code = context.vehicle_profile.engine_code
        term = glossary.render(code) if code else context.vehicle_profile.engine or "—"
        section = self._find_section(context, "engine")
        if (
            context.vehicle_profile.data_origin == DataOrigin.REAL
            and section
            and any(item.status == EvidenceStatus.CONFIRMED for item in section.claims)
        ):
            claims = self._section_text(section)
            text = {
                "ru": f"По данным досье: {claims}",
                "az": f"Dosyeyə əsasən: {claims}",
                "en": f"According to the dossier: {claims}",
            }[language]
            return self._draft_from_section(section, text)
        claim = self._first_claim(context, "engine")
        return self._insufficient(
            language,
            detail={
                "ru": f"Профиль подтверждает только идентификацию {term}; сравнения с другими двигателями в отчёте нет.",
                "az": f"Profil yalnız {term} identifikasiyasını təsdiqləyir; hesabatda başqa mühərriklərlə müqayisə yoxdur.",
                "en": f"The profile confirms only the {term} identity; the snapshot contains no comparison with other engines.",
            }[language],
            source_ids=claim.source_ids if claim else [],
            evidence_ids=claim.evidence_ids if claim else [],
        )

    def _weak_points_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
    ) -> GroundedChatDraft:
        section = self._find_section(context, "weak_points")
        if context.vehicle_profile.data_origin == DataOrigin.REAL and section and section.claims:
            return self._draft_from_section(section, self._section_text(section))
        if not context.known_issues:
            return self._insufficient(language)
        issues = context.known_issues
        names = ", ".join(item.component for item in issues)
        text = {
            "ru": f"Коротко: в досье модели подтверждены пункты: {names}. Это не доказывает наличие проблемы у конкретной машины; применимость отзывной кампании проверяется по VIN, состояние — осмотром.",
            "az": f"Qısa cavab: model dosyesində bu bəndlər təsdiqlənib: {names}. Bu, konkret avtomobildə problemin olmasını sübut etmir; geri çağırma VIN üzrə, vəziyyət baxışla yoxlanılır.",
            "en": f"Short answer: the model-level snapshot confirms these items: {names}. This does not prove the specific car has them; check recall applicability by VIN and condition by inspection.",
        }[language]
        return GroundedChatDraft(
            text=text,
            status=EvidenceStatus.CONFIRMED,
            source_ids=list(dict.fromkeys(source for item in issues for source in item.source_ids)),
            evidence_ids=list(
                dict.fromkeys(evidence for item in issues for evidence in item.evidence_ids)
            ),
        )

    def _section_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
        section_key: str,
        glossary: AbbreviationExplainer,
    ) -> GroundedChatDraft:
        section = self._find_section(context, section_key)
        if not section or not section.claims:
            return self._insufficient(language)
        text = self._section_text(section)
        if section_key == "recalls_tsb":
            prefix = {
                "ru": "По сохранённым данным об отзывных кампаниях и документах производителя: ",
                "az": "Geri çağırmalar və istehsalçı sənədləri üzrə saxlanmış məlumatlara əsasən: ",
                "en": "According to the saved recall and manufacturer-document information: ",
            }[language]
            text = prefix + text
        if section_key == "pre_purchase_check":
            return GroundedChatDraft(
                text=text,
                status=EvidenceStatus.NEEDS_INSPECTION,
                source_ids=list(
                    dict.fromkeys(source for item in section.claims for source in item.source_ids)
                ),
                evidence_ids=list(
                    dict.fromkeys(
                        evidence for item in section.claims for evidence in item.evidence_ids
                    )
                ),
            )
        return self._draft_from_section(section, text)

    @staticmethod
    def _section_text(section) -> str:  # noqa: ANN001
        # Reuse only localized snapshot content, including the inspection actions.
        # Bound long recall/communication sections to the first three records.
        return "\n\n".join(
            " ".join(
                dict.fromkeys(
                    part
                    for part in (
                        claim.heading,
                        claim.text,
                        claim.why_it_matters,
                        claim.applicability,
                        claim.what_to_check,
                    )
                    if part
                )
            )
            for claim in section.claims[:3]
        )

    def _sources_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
    ) -> GroundedChatDraft:
        section = next(
            (
                item
                for item in context.dossier_sections
                if item.claims and item.key != "pre_purchase_check"
            ),
            None,
        )
        if section is None:
            return self._insufficient(language)
        real_count = sum(item.data_origin == DataOrigin.REAL for item in context.sources)
        text = {
            "ru": f"Коротко: в досье подключено реальных источников: {real_count}. В приложении к ответу показаны записи с издателем, URL и датой получения.",
            "az": f"Qısa cavab: dosyedə {real_count} real mənbə var. Cavab əlavəsində nəşriyyat, URL və alınma tarixi göstərilir.",
            "en": f"Short answer: the model dossier contains {real_count} real sources. The answer attachments show publisher, URL and retrieval date.",
        }[language]
        draft = self._draft_from_section(section, text)
        draft.source_ids = self._sources_for_origin(context, DataOrigin.REAL)
        return draft

    def _expensive_issue_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
    ) -> GroundedChatDraft:
        if not context.local_costs:
            return self._insufficient(
                language,
                detail={
                    "ru": "В контексте нет подтверждённых местных цен ремонта, поэтому назвать самое дорогое слабое место нельзя.",
                    "az": "Kontekstdə təsdiqlənmiş yerli təmir qiymətləri yoxdur, buna görə ən bahalı zəif nöqtəni demək olmaz.",
                    "en": "The context has no confirmed local repair prices, so it cannot rank the most expensive weak point.",
                }[language],
            )
        return self._insufficient(language)

    def _seller_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
    ) -> GroundedChatDraft:
        if not context.known_issues:
            return self._insufficient(language, action=True)
        issue = context.known_issues[0]
        text = {
            "ru": f"Коротко: начните с вопроса по узлу «{issue.component}» и попросите подтвердить выполненные работы. Основание отчёта: {issue.description} Действие: {issue.inspection_recommendation}",
            "az": f"Qısa cavab: əvvəlcə «{issue.component}» qovşağı barədə soruşun və görülmüş işlərin təsdiqini istəyin. Hesabat əsası: {issue.description} Addım: {issue.inspection_recommendation}",
            "en": f"Short answer: start by asking about the ‘{issue.component}’ component and request evidence of completed work. Snapshot basis: {issue.description} Action: {issue.inspection_recommendation}",
        }[language]
        return GroundedChatDraft(
            text=text,
            status=issue.status,
            source_ids=issue.source_ids,
            evidence_ids=issue.evidence_ids,
        )

    def _poor_roads_answer(self, language: str) -> GroundedChatDraft:
        return self._insufficient(
            language,
            detail={
                "ru": "В профиле нет подтверждённых данных о клиренсе и применимости подвески к плохим дорогам.",
                "az": "Profildə klirens və asqının pis yollara uyğunluğu barədə təsdiqlənmiş məlumat yoxdur.",
                "en": "The profile has no confirmed ground-clearance or poor-road suitability evidence.",
            }[language],
            action=True,
        )

    def _mileage_answer(
        self,
        context: ChatContextSnapshot,
        language: str,
        mileage: int | None,
    ) -> GroundedChatDraft:
        supported = [
            issue
            for issue in context.known_issues
            if mileage is not None
            and issue.mileage_range is not None
            and issue.mileage_range[0] <= mileage <= issue.mileage_range[1]
        ]
        if supported:
            issue = supported[0]
            text = {
                "ru": f"Коротко: для пробега {mileage:,} км отчёте связывает проверку с узлом «{issue.component}». Основание: {issue.description} Действие: {issue.inspection_recommendation}",
                "az": f"Qısa cavab: {mileage:,} km yürüş üçün hesabat «{issue.component}» qovşağının yoxlanmasını göstərir. Əsas: {issue.description} Addım: {issue.inspection_recommendation}",
                "en": f"Short answer: at {mileage:,} km the snapshot links inspection to the ‘{issue.component}’ component. Basis: {issue.description} Action: {issue.inspection_recommendation}",
            }[language]
            return GroundedChatDraft(
                text=text,
                status=issue.status,
                source_ids=issue.source_ids,
                evidence_ids=issue.evidence_ids,
            )
        mileage_text = f" {mileage:,} км" if mileage and language == "ru" else ""
        detail = {
            "ru": f"Для пробега{mileage_text} в отчёте нет слабых мест с подтверждённым диапазоном пробега.",
            "az": "Bu yürüş üçün hesabatda təsdiqlənmiş yürüş intervalı olan zəif nöqtə yoxdur.",
            "en": "The snapshot has no weak point with a supported mileage range for that mileage.",
        }[language]
        return self._insufficient(language, detail=detail, action=True)

    def _insufficient(
        self,
        language: str,
        *,
        detail: str | None = None,
        action: bool = False,
        source_ids: list[str] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> GroundedChatDraft:
        direct = {
            "ru": "Коротко: уверенного ответа по этому отчёту нет.",
            "az": "Qısa cavab: bu hesabat üzrə əmin cavab yoxdur.",
            "en": "Short answer: this snapshot does not support a confident answer.",
        }[language]
        parts = [direct]
        if detail:
            parts.append(detail)
        parts.append(_INSUFFICIENT[language])
        if action:
            parts.append(
                {"ru": "Действие: ", "az": "Addım: ", "en": "Action: "}[language]
                + _INSPECTION[language]
            )
        return GroundedChatDraft(
            text=" ".join(parts),
            status=(
                EvidenceStatus.NEEDS_INSPECTION if action else EvidenceStatus.INSUFFICIENT_DATA
            ),
            source_ids=source_ids or [],
            evidence_ids=evidence_ids or [],
        )

    @staticmethod
    def _first_source(context: ChatContextSnapshot) -> list[str]:
        return [context.sources[0].id] if context.sources else []

    @staticmethod
    def _sources_for_origin(context: ChatContextSnapshot, origin: DataOrigin) -> list[str]:
        return [item.id for item in context.sources if item.data_origin == origin]

    @staticmethod
    def _find_section(context: ChatContextSnapshot, section_key: str):
        return next((item for item in context.dossier_sections if item.key == section_key), None)

    @staticmethod
    def _draft_from_section(section, text: str) -> GroundedChatDraft:  # noqa: ANN001
        claims = [item for item in section.claims if item.evidence_ids and item.source_ids]
        if not claims:
            return GroundedChatDraft(text=text, status=EvidenceStatus.INSUFFICIENT_DATA)
        status = next(
            s
            for s in (
                EvidenceStatus.INSUFFICIENT_DATA,
                EvidenceStatus.NEEDS_INSPECTION,
                EvidenceStatus.ESTIMATE,
                EvidenceStatus.CONFIRMED,
            )
            if any(item.status == s for item in claims)
        )
        return GroundedChatDraft(
            text=text,
            status=status,
            source_ids=list(dict.fromkeys(source for item in claims for source in item.source_ids)),
            evidence_ids=list(
                dict.fromkeys(evidence for item in claims for evidence in item.evidence_ids)
            ),
        )

    @staticmethod
    def _first_claim(context: ChatContextSnapshot, section_key: str):
        section = next(
            (item for item in context.dossier_sections if item.key == section_key),
            None,
        )
        return section.claims[0] if section and section.claims else None

    @staticmethod
    def _contains(value: str, options: tuple[str, ...]) -> bool:
        return any(option in value for option in options)

    @staticmethod
    def _money_value(question: str) -> Decimal | None:
        compact = question.replace(" ", "").replace(" ", "")
        match = re.search(r"(?<!\d)(\d{4,7})(?!\d)", compact)
        if not match:
            return None
        try:
            return Decimal(match.group(1))
        except InvalidOperation:
            return None

    @staticmethod
    def _remembered_mileage(
        question: str,
        conversation: list[ChatConversationTurn],
    ) -> int | None:
        values = [question] + [
            item.content for item in reversed(conversation) if item.role == ChatRole.USER
        ]
        for value in values:
            thousand = re.search(
                r"(?<!\d)(\d{2,3})\s*(?:тыс(?:яч)?|k\b|min\b)",
                value.casefold(),
            )
            if thousand:
                return int(thousand.group(1)) * 1000
            full = re.search(r"(?<!\d)(\d{4,7})(?!\d)", value.replace(" ", ""))
            if full:
                return int(full.group(1))
        return None

    @staticmethod
    def _mileage_phrase(language: str, mileage: int | None) -> str:
        if mileage is None:
            return ""
        return {
            "ru": f" Вы ранее указали пробег {mileage:,} км.",
            "az": f" Siz əvvəl {mileage:,} km yürüş qeyd etmisiniz.",
            "en": f" You previously stated {mileage:,} km.",
        }[language]

    @staticmethod
    def _glossary(
        language: str,
        conversation: list[ChatConversationTurn],
    ) -> AbbreviationExplainer:
        glossary = AbbreviationExplainer(language)
        assistant_text = " ".join(
            item.content for item in conversation if item.role == ChatRole.ASSISTANT
        )
        for abbreviation in EXPLANATIONS:
            if abbreviation in assistant_text:
                glossary.seen.add(abbreviation)
        return glossary
