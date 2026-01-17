import os
import time
import requests
import re

def get_api_config():
    """
    API_KEY.txt 파일에서 API 키와 모델 이름을 읽어옵니다.
    형식: API_KEY,MODEL_NAME (쉼표로 구분)
    """
    file_path = "API_KEY.txt"
    if not os.path.exists(file_path):
        return "", ""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                return "", ""
            parts = [p.strip() for p in content.split(',')]
            api_key = parts[0].replace('"', '').replace("'", "").strip() if len(parts) > 0 else ""
            model_name = parts[1].replace('"', '').replace("'", "").strip() if len(parts) > 1 else ""
            return api_key, model_name
    except Exception as e:
        print(f"API 설정 파일을 읽는 중 오류 발생: {e}")
        return "", ""

def call_gemini_api(prompt, system_instruction="", cheap_mode=False):   
    """Gemini API를 호출하여 평가 및 채점을 수행합니다."""

    api_key, model_name = get_api_config()
    if not api_key or not model_name:
        print("오류: API_KEY.txt 설정이 올바르지 않습니다.")
        return None

    #cheap_mode : 싼 gemini model로 전환. 총점 구하기용.
    if cheap_mode:
        model_name = 'gemini-2.5-flash-lite'

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    for i in range(5):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "")
            elif response.status_code == 429:
                time.sleep(2**i)
                continue
            else:
                break
        except Exception:
            time.sleep(2**i)
            continue
    return None

def grade_cover_letter():
    """
    자기소개서를 읽고 Rules.txt에 기반한 20가지 항목으로 채점하여 합격 여부를 반환합니다.
    """
    rules_path = "Rules.txt"
    result_path = os.path.join("res", "result.txt")

    # 1. Rules.txt 읽기
    if not os.path.exists(rules_path):
        print("오류: Rules.txt 파일이 필요합니다.")
        return "error"
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_content = f.read().strip()

    # 2. Rules.txt로부터 20가지 채점 요소 도출
    print("Agent_Teacher: Rules.txt로부터 20가지 채점 요소를 도출 중...")
    criteria_prompt = f"""
    아래의 작성 규칙을 바탕으로, 자기소개서를 평가할 수 있는 구체적인 채점 항목 20가지를 리스트 형태로 도출하세요.
    각 항목은 5점 만점으로 채점될 예정입니다 (총점 100점).
    
    [작성 규칙]
    {rules_content}
    """
    criteria = call_gemini_api(criteria_prompt, "당신은 엄격한 인사팀 평가 위원입니다. 평가 지표만 리스트로 출력하세요.")

    print(f'--------------------criteria--------------------\n{criteria}')
    
    # 3. Writer가 작성한 자기소개서 읽기
    if not os.path.exists(result_path):
        print("오류: res/result.txt 파일이 존재하지 않습니다.")
        return "error"
    
    with open(result_path, "r", encoding="utf-8") as f:
        cover_letter = f.read().strip()

    # 4. 자기소개서 채점
    print("Agent_Teacher: 도출된 항목을 바탕으로 자기소개서 채점 시작...")
    grading_prompt = f"""
    [평가 항목]
    {criteria}

    [자기소개서 본문]
    {cover_letter}

    위의 20가지 평가 항목을 바탕으로 자기소개서를 매우 엄격하게 채점하세요.
    각 항목당 5점 만점이며, 다음 내용을 담은 채점표를 작성하세요.
    평가 항목, 평가 내용, 평가 근거, 해당 항목의 점수
    채점표 이외에 다른 내용은 일절 작성하지 마세요.
    """
    
    scorecard = call_gemini_api(grading_prompt, "당신은 매우 보수적인 채용 전문가입니다. 채점표만 작성하세요.")

    print(f'--------------------scorecard--------------------\n{scorecard}')

    # 5. 채점표를 teacher_feedback.txt로 저장
    output_dir = "res"
    file_path = os.path.join(output_dir, "teacher_feedback.txt")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"System: '{output_dir}' 폴더가 생성되었습니다.")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(scorecard)


    # 6. 총점 출력
    print("Agent_Teacher: 도출된 항목을 바탕으로 자기소개서 채점 시작...")
    grading_prompt = f"""
    [채점표]
    {scorecard}

    채점표를 보고 총점을 구하세요.
    총점만 정수로 출력하고 그 외 제외한 어떤 것도 추가하지 마세요.
    """
    
    score_text = call_gemini_api(grading_prompt, "당신은 보수적인 채용 전문가입니다. 채점표를 보고 총점만 말하세요.", cheap_mode=True)
    
    # 숫자 추출
    try:
        score = int(re.sub(r'[^0-9]', '', score_text))
        print(f"최종 평가 점수: {score}점")
        
        # 5. 결과 판단
        if score >= 90:
            print("결과: PASS (yes)")
            return "yes"
        else:
            print("결과: FAIL (no)")
            return "no"
    except Exception as e:
        print(f"점수 파싱 오류: {score_text}")
        return "error"

if __name__ == "__main__":
    grade_cover_letter()
