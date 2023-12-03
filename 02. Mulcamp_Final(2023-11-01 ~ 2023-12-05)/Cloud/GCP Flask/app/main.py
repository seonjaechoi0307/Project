from flask import Flask, request, jsonify
from google.cloud import bigquery

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

## 카카오톡 텍스트형 응답
@app.route('/api/sayHello', methods=['POST'])
def sayHello():
    body = request.get_json()
    print(body)
    print(body['userRequest']['utterance'])

    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "안녕 hello I'm Ryan"
                    }
                }
            ]
        }
    }

    return responseBody


## 카카오톡 이미지형 응답
@app.route('/api/showHello', methods=['POST'])
def showHello():
    body = request.get_json()
    print(body)
    print(body['userRequest']['utterance'])

    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleImage": {
                        "imageUrl": "https://t1.daumcdn.net/friends/prod/category/M001_friends_ryan2.jpg",
                        "altText": "hello I'm Ryan"
                    }
                }
            ]
        }
    }

    return responseBody

# 설비 데이터의 특정 조건 데이터 개수를 파악하는 함수
def count_dz2_op_signal(status):
    client = bigquery.Client()
    query = f"""
        SELECT COUNT(DZ2_OP_Signal) as count
        FROM `mulcamp-action-lab15.database.machine`
        WHERE `DZ2_OP_Signal` = {status}
    """
    query_job = client.query(query)
    result = query_job.result()

    # 첫 번째 행 가져오기
    first_row = next(result, None)
    return first_row.count if first_row else 0

# 경고 메시지 전달하는 Flask 라우트
@app.route('/api/showdata', methods=['POST'])
def showdata():
    safe_count = count_dz2_op_signal(0)  # 안전한 상태의 데이터 개수
    danger_count = count_dz2_op_signal(1)# 위험한 상태의 데이터 개수

    total = safe_count + danger_count
    if total > 0:
        danger_percentage = (danger_count / total) * 100
    else:
        danger_percentage = 0
    
    message = f"DZ2_OP_Signal 설비는\n" \
              f"총 {total}시간 중\n" \
              f"안전 작업: {safe_count}시간 안전\n" \
              f"위험 작업: {danger_count}시간 위험\n" \
              f"작업 위험률: {danger_percentage:.2f}% 위험했습니다."
    
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": message
                    }
                }
            ]
        }
    }

    return jsonify(responseBody)


# 월별 작업시간, 위험률, 위험률 랭크를 불러오는 쿼리
@app.route('/api/showrank', methods=['POST'])
def Month_By_Danger_Rank():
    client = bigquery.Client()

    # SQL 쿼리 정의
    query = """
        SELECT *, DENSE_RANK() OVER(ORDER BY D_Rate DESC) AS RNK
        FROM (
            SELECT
                Month,
                COUNT(Month) AS M_Count,
                ROUND(SUM(DZ2_OP_Signal) / COUNT(DZ2_OP_Signal) * 100, 2) as D_Rate
            FROM `mulcamp-action-lab15.database.machine`
            GROUP BY Month
        ) A
        ORDER BY Month;
    """

    # 쿼리 실행
    query_job = client.query(query)
    results = query_job.result()

    # 결과 처리 및 메시지 구성
    month_details = []
    highest_risk_month = None
    highest_risk_rate = None

    # 개별 메시지 구성 로직
    for row in results:
        month_detail = f"{row.Month}월 설비 위험률: {row.D_Rate}%, 위험 순위: {row.RNK}"
        month_details.append(month_detail)
        if row.RNK == 1:
            highest_risk_month = row.Month
            highest_risk_rate = row.D_Rate

    # 전체 메시지 구성
    message = "\n".join(month_details)
    if highest_risk_month and highest_risk_rate:
        message += f"\n\n가장 위험했던 {highest_risk_month}월, 위험률: {highest_risk_rate}%"

    # JSON 형식으로 변환
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": message
                    }
                }
            ]
        }
    }

    return responseBody