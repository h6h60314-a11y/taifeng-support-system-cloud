from db import init_db, insert_arrival, insert_departure, insert_support_request


def main():
    init_db()
    insert_support_request(
        request_no="REQ20260408001",
        request_team="出貨課－出貨組",
        publish_time="2026-04-08 08:30:00",
        required_count=2,
        reason="早班訂單量增加，需要臨時補人",
        priority="高",
        note="請優先支援揀貨區",
        status="支援中",
    )
    insert_support_request(
        request_no="REQ20260408002",
        request_team="企劃課－行政組",
        publish_time="2026-04-08 09:00:00",
        required_count=1,
        reason="臨時資料整理與報表彙整",
        priority="中",
        note="需熟悉 Excel 操作",
        status="待支援",
    )
    insert_departure(
        name="王小明",
        origin_team="進貨課－進貨組",
        target_team="出貨課－出貨組",
        depart_time="2026-04-08 08:45:00",
        request_no="REQ20260408001",
        status="已離組",
    )
    insert_arrival(
        name="王小明",
        origin_team="進貨課－進貨組",
        arrival_team="出貨課－出貨組",
        arrival_time="2026-04-08 08:55:00",
        request_no="REQ20260408001",
        status="已到組",
    )
    print("範例資料初始化完成。")


if __name__ == "__main__":
    main()
