import os
import time
import requests
import shutil

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

def write_cover_letter(attempt=1):
    """
    4개의 분석 파일을 통합하여 자기소개서를 작성합니다.
    attempt 인자를 받아 파일명을 결정합니다.
    """
    # 시도 횟수에 따른 파일명 설정 (예: result_attempt1.txt)
    filename = f"result_attempt{attempt}.txt"
    output_path = os.path.join("res", filename)
    # Teacher 에이전트가 참조할 기본 파일명도 유지 (선택 사항)
    default_output_path = os.path.join("res", "result.txt")

    
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

    print(f"Agent_Writer: (시도 {attempt}) 자기소개서 작성을 시작합니다...")



    #3. 프롬프트 구성
    if attempt == 1: #첫 번째 시도일 때
        system_prompt = (
            "당신은 최고의 대기업 취업 컨설턴트입니다. "
            "제공된 소스 데이터를 융합하여 지원자의 경험이 기업의 인재상과 직무 역량에 부합하도록 자소서를 작성하세요."
        )
        
        user_prompt = f"""
        아래 제공된 [데이터 소스]의 내용을 바탕으로 자기소개서를 작성해주세요.

        [데이터 소스 1: 기업 분석]
        {company_data}

        [데이터 소스 2: 지원자 역량]
        {applicant_data}

        [데이터 소스 3: 프로젝트 상세]
        {project_data}

        [작성 가이드라인]
        {rules}

        ---
        각 항목은 매력적인 소제목을 포함하여 4가지 항목을 작성하세요.
        1. 지원동기 (1000자)
        2. 직무 관련 역량/경험 1 (1000자)
        3. 직무 관련 역량/경험 2 (1000자)
        4. 성격의 장단점 (1000자)
        """
    else: #그 외
        
        previous_result = read_res_file("result.txt")
        teacher_feedback = read_res_file("teacher_feedback.txt")
        
        system_prompt = (
            "당신은 최고의 대기업 취업 컨설턴트입니다. "
            "이전 작성물과 전문가의 피드백을 분석하여, 지적된 사항을 완벽히 보완한 수정본을 작성하는 것이 당신의 임무입니다."
        )
        
        user_prompt = f"""
        이전 시도에서 작성된 자기소개서에 대해 전문가의 피드백이 접수되었습니다. 
        피드백 내용을 엄격히 반영하여 기존 내용을 대폭 수정 및 보완해주세요.
        
        아래 제공된 [데이터 소스]의 내용을 바탕으로 자기소개서를 보완해주세요.

        [데이터 소스 1: 기업 분석]
        {company_data}

        [데이터 소스 2: 지원자 역량]
        {applicant_data}

        [데이터 소스 3: 프로젝트 상세]
        {project_data}

        [작성 가이드라인]
        {rules}

        ---
        [기존 자기소개서]
        {previous_result}

        [전문가 피드백 (반드시 반영할 것)]
        {teacher_feedback}
        """
        

    # 4. API 호출
    draft = call_gemini_api(user_prompt, system_prompt)

    
    if draft:
        if not os.path.exists("res"): os.makedirs("res")
        
        # 1) 시도별 파일 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(draft)
        
        # 2) Teacher가 읽을 수 있도록 result.txt로 복사 (Teacher 코드를 수정하지 않아도 됨)
        with open(default_output_path, "w", encoding="utf-8") as f:
            f.write(draft)
            
        print(f"성공: 자기소개서가 '{output_path}'에 저장되었습니다.")
        return True
    return False

if __name__ == "__main__":
    write_cover_letter()
