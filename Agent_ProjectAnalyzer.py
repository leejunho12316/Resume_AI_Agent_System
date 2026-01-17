import os
import time
import requests
import base64

# Word 파일 처리를 위해 추가
try:
    from docx import Document
except ImportError:
    pass

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

def extract_text_from_docx(file_path):
    """Word 파일에서 텍스트를 추출합니다."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception:
        return ""

def call_gemini_api(prompt, file_path=None, system_instruction=""):
    # 파일에서 API 키와 모델 로드
    api_key, model_name = get_api_config()
    
    if not api_key or not model_name:
        print("오류: API_KEY.txt 설정이 올바르지 않습니다.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    parts = []
    
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            # PDF는 바이너리로 전달
            with open(file_path, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode('utf-8')
            parts.append({"inlineData": {"mimeType": "application/pdf", "data": base64_data}})
        else:
            # Word나 기타 파일은 텍스트로 추출
            extracted_text = extract_text_from_docx(file_path) if ext == ".docx" else ""
            if not extracted_text:
                try:
                    with open(file_path, "r", encoding="utf-8") as f: extracted_text = f.read()
                except: pass
            prompt = f"이 포트폴리오 파일의 내용입니다:\n\n{extracted_text}\n\n{prompt}"

    parts.append({"text": prompt})
    
    payload = {
        "contents": [{"parts": parts}],
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
        except Exception:
            time.sleep(2**i)
            continue
    return None

def analyze_project_info(file_path):
    output_path = os.path.join("res", "Project_data.txt")
    print(f"프로젝트 분석 중: {os.path.basename(file_path)}")
    
    system_prompt = (
        "당신은 기술 면접관입니다. 포트폴리오 파일을 분석해 프로젝트 별 내용을 분석해 주세요. 각 프로젝트는 다음의 내용을 포함해야 합니다.\n"
        "1. 프로젝트명  2. 프로젝트 개요와 목표 3. 사용 기술 4. 문제 해결 과정 5. 결과, 성과"
    )
    user_prompt = "첨부된 포트폴리오 내용을 분석하여 프로젝트 분석 보고서를 작성해줘."
    
    analysis_result = call_gemini_api(user_prompt, file_path, system_prompt)
    
    if analysis_result:
        if not os.path.exists("res"): os.makedirs("res")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        print(f"성공: 프로젝트 분석 결과가 '{output_path}'에 저장되었습니다.")
        return True
    return False
