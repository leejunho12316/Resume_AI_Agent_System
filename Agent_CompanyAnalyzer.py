import os
import time
import requests
import json

def get_api_config():
    """
    API_KEY.txt 파일에서 API 키와 모델 이름을 읽어옵니다.
    형식: API_KEY,MODEL_NAME (쉼표로 구분)
    """
    file_path = "API_KEY.txt"
    if not os.path.exists(file_path):
        return "", ""
    try:
        # utf-8-sig는 윈도우 메모장 등에서 붙는 BOM 문자를 자동으로 제거합니다.
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                return "", ""
            
            # 쉼표(,)를 기준으로 분리합니다.
            parts = [p.strip() for p in content.split(',')]
            
            # 따옴표나 기타 공백이 포함되어 있을 경우를 대비해 정밀하게 정제합니다.
            api_key = parts[0].replace('"', '').replace("'", "").strip() if len(parts) > 0 else ""
            model_name = parts[1].replace('"', '').replace("'", "").strip() if len(parts) > 1 else ""
            
            return api_key, model_name
    except Exception as e:
        print(f"API 설정 파일을 읽는 중 오류 발생: {e}")
        return "", ""

def call_gemini_api(prompt, system_instruction=""):
    api_key, model_name = get_api_config()
    
    if not api_key:
        print("오류: API 키가 비어 있습니다. API_KEY.txt 내용을 확인하세요.")
        return None
    if not model_name:
        print("오류: 모델명이 비어 있습니다. API_KEY.txt의 두 번째 항목을 확인하세요.")
        return None

    # URL 생성 시 모델명에 공백 등이 섞이지 않도록 재확인
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
                # 할당량 초과 시 지수 백오프 적용
                time.sleep(2**i)
                continue
            else:
                # 400 에러 발생 시 에러 메시지 상세 출력
                print(f"API 호출 에러 (Status {response.status_code}):")
                print(response.text)
                # API 키가 유효하지 않다는 메시지가 있으면 즉시 중단
                if "API key not valid" in response.text:
                    print("팁: API_KEY.txt 파일에 오타나 불필요한 공백, 따옴표가 없는지 확인하세요.")
                break
        except Exception as e:
            print(f"네트워크 오류: {e}")
            time.sleep(2**i)
            continue
    return None

def analyze_company_info():
    input_path = os.path.join("res", "job_description.txt")
    output_path = os.path.join("res", "Company_data.txt")
    
    if not os.path.exists(input_path):
        print(f"오류: {input_path} 파일이 존재하지 않습니다. 먼저 WebCrawling을 실행하세요.")
        return False
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            job_content = f.read()
    except Exception as e:
        print(f"공고 파일 읽기 실패: {e}")
        return False
        
    print("Gemini API를 사용하여 기업 분석을 시작합니다...")
    
    system_prompt = (
        "당신은 전문 채용 컨설턴트입니다. 채용 공고를 분석하여 정리해 주세요.\n"
        "1. 기업 명칭/분야 2. 주요 직무 3. 필수 요건 4. 우대 사항 5. 기술 스택 6. 기업 문화 7. 전략적 팁"
    )
    user_prompt = f"다음 채용 공고를 분석해줘:\n\n{job_content}"
    
    analysis_result = call_gemini_api(user_prompt, system_prompt)
    
    if analysis_result:
        try:
            if not os.path.exists("res"): os.makedirs("res")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(analysis_result)
            print(f"성공: 분석 결과가 '{output_path}'에 저장되었습니다.")
            return True
        except Exception as e:
            print(f"결과 저장 실패: {e}")
            return False
    return False

if __name__ == "__main__":
    analyze_company_info()
