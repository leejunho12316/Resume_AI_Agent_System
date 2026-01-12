import os
import time
import requests

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

def call_gemini_api(prompt, system_instruction=""):
    """Gemini API를 호출하여 자기소개서를 생성합니다."""
    api_key, model_name = get_api_config()
    if not api_key or not model_name:
        print("오류: API_KEY.txt 설정이 올바르지 않습니다.")
        return None

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
                print(f"API 호출 에러 (Status {response.status_code}): {response.text}")
                break
        except Exception as e:
            print(f"네트워크 오류: {e}")
            time.sleep(2**i)
            continue
    return None

def read_res_file(filename):
    """res 폴더 내의 파일을 읽어옵니다."""
    path = os.path.join("res", filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""
    return ""

def write_cover_letter():
    """4개의 분석 파일을 통합하여 자기소개서를 작성합니다."""
    output_path = os.path.join("res", "result.txt")
    
    # 1. 모든 분석 데이터 로드 (텍스트 추출)
    company_data = read_res_file("Company_data.txt")
    applicant_data = read_res_file("Applicant_data.txt")
    project_data = read_res_file("Project_data.txt")
    
    # 2. 작성 규칙 로드
    rules_path = "Rules.txt"
    rules = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = f.read().strip()
    else:
        rules = "전문적인 비즈니스 톤을 유지할 것."

    if not company_data or not applicant_data:
        print("오류: 분석 데이터가 부족하여 작성을 시작할 수 없습니다.")
        return False

    print("Agent_Writer: 4개의 소스 파일을 분석하여 자기소개서 작성을 시작합니다...")

    # 3. 구조화된 프롬프트 구성 (텍스트 삽입 방식)
    system_prompt = (
        "당신은 최고의 대기업 취업 컨설턴트입니다. "
        "제공된 4가지 소스 데이터를 융합하여 지원자의 경험이 기업의 인재상과 직무 역량에 완벽히 부합하도록 자소서를 작성하세요."
    )
    
    user_prompt = f"""
아래 제공된 [데이터 소스]의 내용을 바탕으로 자기소개서를 작성해주세요.
모든 내용은 [작성 가이드라인]을 엄격히 준수해야 합니다.

[데이터 소스 1: 기업 분석]
{company_data}

[데이터 소스 2: 지원자 역량]
{applicant_data}

[데이터 소스 3: 프로젝트 상세]
{project_data}

[작성 가이드라인: Rules.txt]
{rules}

---

위 데이터를 바탕으로 다음 4가지 항목을 작성하세요. 
각 항목은 매력적인 소제목을 포함해야 하며, 구체적인 수치나 기술 스택을 언급하여 신뢰도를 높이세요.

1. 지원동기: 기업의 최근 행보와 지원자의 커리어 목표를 연결하세요.
2. 직무 관련 역량/경험: [프로젝트 상세]의 내용을 활용하여 성과 위주로 작성하세요.
3. 성장과정: 지원자의 가치관이 직무에 어떻게 긍정적 영향을 미칠지 설명하세요.
4. 성격의 장단점: 장점은 극대화하고 단점은 직무 수행에 지장이 없는 선에서 보완 과정을 명시하세요.

작성 결과만 출력해주세요.
"""

    # 4. API 호출
    draft = call_gemini_api(user_prompt, system_prompt)
    
    if draft:
        if not os.path.exists("res"): os.makedirs("res")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(draft)
        print(f"성공: 자기소개서가 생성되어 '{output_path}'에 저장되었습니다.")
        return True
    return False

if __name__ == "__main__":
    write_cover_letter()
