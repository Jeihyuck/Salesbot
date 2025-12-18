import sys

sys.path.append("/www/alpha/")
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")

import django
from django.db import connection

import pandas as pd
import warnings
import datetime

warnings.filterwarnings("ignore")


def get_event_info_model_code(model_codes, site_cd):
    # Standard column schema
    columns = [
        "Model Code",
        "Event Name",
        "Benefit Name",
        "Benefit Description",
        "Benefit Caution",
        "Benefit Start Date",
        "Benefit End Date"
    ]
    empty_df = pd.DataFrame(columns=columns)

    # unique, non-empty model codes
    model_codes = list({c for c in model_codes if c})
    if not model_codes:
        return empty_df

    now = datetime.datetime.now()

    # Query returns columns
    query = """
        SELECT
            mc                 AS "Model Code",
            a.event_nm         AS "Event Name",
            a.benefit_nm       AS "Benefit Name",
            a.benefit_desc     AS "Benefit Description",
            a.benefit_caution  AS "Benefit Caution",
            a.benefit_strt_dtm AS "Benefit Start Date",
            a.benefit_end_dtm  AS "Benefit End Date"
        FROM rubicon_v3_event_map a
        JOIN LATERAL unnest(a.mdl_code) AS mc ON TRUE
        WHERE mc = ANY(%s::varchar[])
          AND a.site_cd = %s
          AND (a.benefit_strt_dtm IS NULL OR a.benefit_strt_dtm <= %s)
          AND (a.benefit_end_dtm  IS NULL OR a.benefit_end_dtm  >= %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                model_codes,                   # Model codes to search
                site_cd,                       # B2C / FN
                now,                           # For date filtering
                now                            # For date filtering
            ),
        )
        rows = cursor.fetchall()
        if not rows:
            return empty_df
        df = pd.DataFrame(rows, columns=[col.name for col in cursor.description])

    df = df.drop_duplicates().reset_index(drop=True)

    return df


def get_event_info_embedding(query_embedding, threshold, site_cd):
    # Standard column schema
    columns = [
        "Model Code",
        "Event Name",
        "Benefit Name",
        "Benefit Description",
        "Benefit Caution",
        "Benefit Start Date",
        "Benefit End Date"
    ]
    empty_df = pd.DataFrame(columns=columns)

    now = datetime.datetime.now()

    # Query returns columns with both event and benefit embedding search
    query = """
        SELECT
            mc                 AS "Model Code",
            a.event_nm         AS "Event Name",
            a.benefit_nm       AS "Benefit Name",
            a.benefit_desc     AS "Benefit Description",
            a.benefit_caution  AS "Benefit Caution",
            a.benefit_strt_dtm AS "Benefit Start Date",
            a.benefit_end_dtm  AS "Benefit End Date"
        FROM rubicon_v3_event_map a
        JOIN LATERAL unnest(a.mdl_code) AS mc ON TRUE
        WHERE a.site_cd = %s
          AND (a.benefit_strt_dtm IS NULL OR a.benefit_strt_dtm <= %s)
          AND (a.benefit_end_dtm  IS NULL OR a.benefit_end_dtm  >= %s)
          AND (
              1 - (a.event_embedding <=> %s::vector) >= %s
              OR 1 - (a.benefit_embedding <=> %s::vector) >= %s
          )
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                site_cd,                       # B2C / FN
                now,                           # For date filtering
                now,                           # For date filtering 
                str(query_embedding),          # For event embedding threshold check
                threshold,                     # Threshold
                str(query_embedding),          # For benefit embedding threshold check
                threshold                      # Threshold
            ),
        )
        rows = cursor.fetchall()
        if not rows:
            return empty_df
        df = pd.DataFrame(rows, columns=[col.name for col in cursor.description])

    df = df.drop_duplicates().reset_index(drop=True)

    return df


def event_manager(
    query_embedding, extended_info_result, country_code, site_cd, threshold=0.65
):

    # Initialize empty DataFrame
    columns = [
        "Model Code",
        "Event Name",
        "Benefit Name",
        "Benefit Description",
        "Benefit Caution",
        "Benefit Start Date",
        "Benefit End Date"
    ]

    empty_df = pd.DataFrame(columns=columns)

    # Conduct structural promotion event search with extended info

    # Take up to 3 codes if only one item, else 1 per item
    n_item = 3 if len(extended_info_result) == 1 else 1

    # Only get promotion event info for KR (data limitation)
    if country_code != "KR":
        return [], empty_df

    # Collect unique model codes
    model_codes = {
        mc
        for item in extended_info_result
        for mc in (item.get("extended_info") or [])[:n_item]
        if mc
    }

    # Fetch event info for the collected model codes
    event_df = get_event_info_model_code(list(model_codes), site_cd)

    # Consolidate by Benefit Name
    meta_cols = [
        "Event Name",
        "Benefit Description",
        "Benefit Caution",
        "Benefit Start Date",
        "Benefit End Date",
    ]

    def first_non_null(series):
        return next((v for v in series if pd.notna(v)), None)

    # Groupby event_nm and benefit_nm
    grouped_df = event_df.groupby(["Event Name", "Benefit Name"], as_index=False).agg(
        {
            "Model Code": lambda s: ",".join(sorted(set(filter(None, s)))),
            **{c: first_non_null for c in meta_cols},
        }
    )

    if not grouped_df.empty:

        grouped_df = grouped_df[
            [
                "Model Code",
                "Event Name",
                "Benefit Name",
                "Benefit Description",
                "Benefit Caution",
                "Benefit Start Date",
                "Benefit End Date",
            ]
        ]

        grouped_df = grouped_df.sort_values("Event Name", ascending=True).reset_index(drop=True)

        event_model_codes = set(",".join(grouped_df["Model Code"]).split(","))
        event_extended = [
            item
            for item in extended_info_result
            if any(mc in event_model_codes for mc in item.get("extended_info", []))
        ]

        # Cut extended_info_result to top 3 items
        top_K = 3

        # Check if Galaxy S25 Series
        mapping_list = [item.get("mapping_code", "") for item in event_extended]
        if set(
            ["갤럭시 S25 울트라", "갤럭시 S25+", "갤럭시 S25", "갤럭시 S25 엣지"]
        ).issubset(set(mapping_list)):
            top_K = 4

        event_extended = event_extended[:top_K]

        return event_extended, grouped_df

    # If Extended Info Result is empty or
    # No structured promotions events were found,
    # Run an embedding search with the rewritten query embedding as input
    
    elif grouped_df.empty:

        # If no grouped_df, use embedding search
        event_df = get_event_info_embedding(query_embedding, threshold, site_cd)

        if event_df.empty:
            return [], empty_df

        event_df["Model Code"] = None

        grouped_df = event_df.groupby(["Event Name", "Benefit Name"], as_index=False).agg(
        {
            "Model Code": lambda s: ",".join(sorted(set(filter(None, s)))),
            **{c: first_non_null for c in meta_cols},
        }
    )

        grouped_df = grouped_df[
            [
                "Model Code",
                "Event Name",
                "Benefit Name",
                "Benefit Description",
                "Benefit Caution",
                "Benefit Start Date",
                "Benefit End Date",
            ]
        ]

        grouped_df = grouped_df.sort_values("Event Name", ascending=True).reset_index(drop=True)

        event_extended = []

        return event_extended, grouped_df


if __name__ == "__main__":
    django.setup()
    from rich import print as rich_print
    from rich.table import Table
    from rich.console import Console
    from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank

    country_code = "KR"
    site_cd = "B2C"
    mentioned_products = []
    threshold = 0.65

    test_type = "extended"  # manual or extended
    
    # Extended Info with model
    # test_query = "갤럭시 S25 행사 뭐 있어?"
    test_query = "Bespoke 의류케어 으뜸효율 기획전 행사 있어?"
    test_query = "Bespoke 정수기 행사가 뭐야?"
    test_query = "RWP71411AABA 제품이 Bespoke 정수기 행사에 포함되나요?"
    #test_query = "의류케어 으뜸효율 기획전이 뭐야?"
    #test_query = "의류케어 제품 관련 행사/프로모션 있어?"
    #test_query = "으뜸효율 AI 김치플러스 행사가 뭐야?"
    #test_query = "으뜸효율 Bespoke AI 냉장고 행사가 뭐야?"5
    #test_query = "에어케어 제품 관련 행사/프로모션 있어?"

    # Embedding search queries
    #test_query = "으뜸효율가전 행사가 있어?"
    #test_query = "퍼실 딥클린 파워젤 증정해주는 혜택이 뭐지?"

    # Extended Info no model
    #test_query = "큐커 개구리에디션 2000L 지금 진행중인 있어?"

    query_embedding = embedding_rerank.baai_embedding(test_query, "test")[0]

    if test_type == "manual":
        # Test 1: Manual Input
        extended_code_mapping = [
            {"id": "123", "extended_info": ["LS49DG952SKXKR", "LS32FM902SKXKR"]},
            {"id": "456", "extended_info": ["LS27D800UAKXKR"]},
        ]

        event_extended, event_df = event_manager(
            query_embedding, extended_code_mapping, country_code, site_cd, threshold
        )

        rich_print(f"Event Extended: \n {event_extended}\n")
        rich_print(f"Event DataFrame: \n {event_df}\n")

    elif test_type == "extended":
        # Test 2: Retrieve Extended Info
        from apps.rubicon_v3.__function import __embedding_rerank as embedding_rerank
        from apps.rubicon_v3.__function import _10_rewrite as rewrite
        from apps.rubicon_v3.__function import (
            _22_orchestrator_intelligence as intelligence_triage,
        )
        from apps.rubicon_v3.__function import (
            _20_orchestrator_NER_init,
            _23_orchestrator_correction,
            _30_orchestrator_NER_standardization,
        )
        from apps.rubicon_v3.__function import (
            _21_orchestrator_query_analyzer as query_analyzer,
        )
        from apps.rubicon_v3.__function import (
            _31_orchestrator_assistant as assistant_v2,
        )
        from apps.rubicon_v3.__function import _60_complement as complementation
        from apps.rubicon_v3.__function import _44_date_match as date_match
        from apps.rubicon_v3.__function import _32_sub_intelligence as sub_intelligence

        def get_complement_result(
            test_query, test_country_code, mentioned_products, site_cd
        ):

            test_query = rewrite.re_write_history(
                original_query=test_query,
                files=[],
                message_history=[],
                mentioned_products=[],
                country_code=test_country_code,
                channel="DEV Debug",
            )["re_write_query_list"][0]

            embedded_test_query = embedding_rerank.baai_embedding(test_query, "test")[0]

            test_intelligence = intelligence_triage.intelligence(
                top_query=test_query, country_code=test_country_code
            )

            test_sub_intelligence = sub_intelligence.get_sub_intelligence(
                test_query, test_intelligence, test_country_code
            )
            test_ner_result, _ = _20_orchestrator_NER_init.ner(
                test_query, embedded_test_query, test_country_code
            )
            query_analysis = query_analyzer.query_analyzer(
                top_query=test_query, message_history=[], country_code=test_country_code
            )

            test_ner_result, _, _ = _23_orchestrator_correction.correction(
                test_ner_result,
                test_intelligence,
                query_analysis,
                "DEV Debug",
                test_country_code,
            )

            new_ner_result = (
                _30_orchestrator_NER_standardization.standardize_ner_expression(
                    test_ner_result, test_country_code
                )
            )
            date_list = date_match.match_and_parse_datetime(
                new_ner_result, test_country_code, "test"
            )

            _RAG_depth = query_analysis.get("RAG_depth", "")
            _query_type = query_analysis.get("query_type", "")
            _data_filter = query_analysis.get("data_filter", "")

            test_assistant_result = assistant_v2.assistant(
                test_query,
                [],
                test_country_code,
                _RAG_depth,
                _query_type,
                test_ner_result,
                test_intelligence,
                "gpt-4.1-mini",
            )

            qc_result = complementation.complement(
                test_query,
                embedded_test_query,
                query_analysis,
                test_intelligence,
                test_sub_intelligence,
                test_ner_result,
                new_ner_result,
                test_assistant_result,
                date_list,
                test_country_code,
                "",
                "test",
                "",
                180,
                "DEV Debug",
                mentioned_products,
                site_cd,
            )
            return qc_result

        rich_print("[green]Retrieving extended info for query: ", test_query)
        qc_result = get_complement_result(
            test_query, country_code, mentioned_products, site_cd
        )
        # rich_print(f"Complement Result: \n {qc_result}\n")
        extended_info_result = qc_result.get("extended_info_result", [])

        rich_print(f"Extended Info Result: \n {extended_info_result}\n")
        event_extended, event_df = event_manager(
            query_embedding, extended_info_result, country_code, site_cd, threshold
        )
        rich_print(f"Filtered Event Extended: \n {event_extended}\n")
        
        filter_columns = ["Model Code", "Event Name", "Benefit Name", "Benefit Description"]
        filtered_event_df = event_df[filter_columns]
        
        rich_print("Event DataFrame:")

        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        for col in filter_columns:
            table.add_column(col)
        for _, row in filtered_event_df.iterrows():
            table.add_row(*(str(row[col]) if row[col] is not None else "" for col in filter_columns))
        console.print(table)
        
        #rich_print(f"Event DataFrame: \n {filtered_event_df}\n")
