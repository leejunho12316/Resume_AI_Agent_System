import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os

# 각 에이전트 모듈에서 함수를 불러옵니다.
from WebCrawling import save_job_posting_to_txt
from Agent_CompanyAnalyzer import analyze_company_info
from Agent_ApplicantAnalyzer import analyze_applicant_info
from Agent_ProjectAnalyzer import analyze_project_info
from Agent_Writer import write_cover_letter
from Agent_Teacher import grade_cover_letter

# 글로벌 변수로 파일 경로 저장
resume_path = ""
portfolio_path = ""

def select_resume():
    """이력서 파일을 선택합니다."""
    global resume_path
    file = filedialog.askopenfilename(
        title="이력서 선택",
        filetypes=[("Document files", "*.pdf *.docx *.doc"), ("All files", "*.*")]
    )
    if file:
        resume_path = file
        resume_label.config(text=f"이력서: {os.path.basename(file)}", fg="black")

def select_portfolio():
    """포트폴리오 파일을 선택합니다."""
    global portfolio_path
    file = filedialog.askopenfilename(
        title="포트폴리오 선택",
        filetypes=[("Document files", "*.pdf *.docx *.doc"), ("All files", "*.*")]
    )
    if file:
        portfolio_path = file
        portfolio_label.config(text=f"포트폴리오: {os.path.basename(file)}", fg="black")

def start_analysis_workflow():
    """
    1단계: 분석 워크플로우 (크롤링 -> 기업 -> 지원자 -> 프로젝트 분석)
    """
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("입력 오류", "채용공고 URL을 입력해주세요.")
        return
    
    status_label.config(text="1단계: 웹 크롤링 진행 중...", fg="blue")
    analysis_button.config(state=tk.DISABLED)
    
    def run_process():
        try:
            if not save_job_posting_to_txt(url, "job_description.txt"):
                raise Exception("웹 크롤링에 실패했습니다.")

            root.after(0, lambda: status_label.config(text="2단계: Gemini AI 기업 분석 진행 중...", fg="purple"))
            if not analyze_company_info():
                raise Exception("기업 분석에 실패했습니다.")

            if resume_path:
                root.after(0, lambda: status_label.config(text="3단계: 지원자 역량 분석 진행 중...", fg="#E67E22"))
                if not analyze_applicant_info(resume_path):
                    raise Exception("지원자 분석에 실패했습니다.")

            if portfolio_path:
                root.after(0, lambda: status_label.config(text="4단계: 포트폴리오 프로젝트 분석 진행 중...", fg="#16A085"))
                if not analyze_project_info(portfolio_path):
                    raise Exception("프로젝트 분석에 실패했습니다.")

            root.after(0, lambda: status_label.config(text="완료: 모든 분석 데이터가 res 폴더에 저장되었습니다.", fg="green"))
            root.after(0, lambda: messagebox.showinfo("성공", "기초 데이터 분석이 완료되었습니다!\n이제 자기소개서 작성을 시작할 수 있습니다."))
            root.after(0, lambda: writer_button.config(state=tk.NORMAL))

        except Exception as e:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: status_label.config(text=f"오류: {msg}", fg="red"))
            root.after(0, lambda msg=error_msg: messagebox.showerror("실패", msg))
        finally:
            root.after(0, lambda: analysis_button.config(state=tk.NORMAL))

    threading.Thread(target=run_process, daemon=True).start()

def start_writing_workflow():
    """
    2단계: 자기소개서 작성 및 자동 첨삭 루프 (Writer -> Teacher)
    """
    # 분석 파일 존재 확인
    if not os.path.exists(os.path.join("res", "Company_data.txt")) or not os.path.exists(os.path.join("res", "Applicant_data.txt")):
        messagebox.showwarning("데이터 부족", "먼저 '통합 분석 시작'을 통해 기초 데이터를 생성해야 합니다.")
        return

    writer_button.config(state=tk.DISABLED)
    status_label.config(text="Writer: 자기소개서 초안을 작성하고 있습니다...", fg="blue")

    def run_writing_loop():
        attempt = 1
        try:
            while True:
                root.after(0, lambda a=attempt: status_label.config(text=f"시도 {a}: Writer가 자기소개서를 작성 중입니다...", fg="#2980B9"))
                
                # 1. Writer 실행
                if not write_cover_letter():
                    raise Exception("자기소개서 작성 중 API 오류가 발생했습니다.")

                # 2. Teacher 실행
                root.after(0, lambda a=attempt: status_label.config(text=f"시도 {a}: Teacher가 자기소개서를 채점 중입니다...", fg="#8E44AD"))
                result = grade_cover_letter()

                if result == "yes":
                    root.after(0, lambda: status_label.config(text="최종 합격: 자기소개서 작성이 완료되었습니다!", fg="green"))
                    root.after(0, lambda: messagebox.showinfo("축하합니다!", f"{attempt}번의 수정 끝에 Teacher 에이전트의 승인을 받았습니다.\n결과: res/result.txt"))
                    break
                elif result == "no":
                    attempt += 1
                    root.after(0, lambda a=attempt: status_label.config(text=f"재작성: 점수가 낮아 다시 작성합니다. (시도 {a})", fg="#E67E22"))
                    time_sleep = 2 # 잠깐의 대기
                    continue
                else:
                    raise Exception("Teacher 에이전트가 점수를 산출하지 못했습니다. (error)")

        except Exception as e:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: status_label.config(text=f"작성 오류: {msg}", fg="red"))
            root.after(0, lambda msg=error_msg: messagebox.showerror("실패", msg))
        finally:
            root.after(0, lambda: writer_button.config(state=tk.NORMAL))

    threading.Thread(target=run_writing_loop, daemon=True).start()

# --- GUI 레이아웃 설정 ---
root = tk.Tk()
root.title("AI 자소서 자동화 시스템 (Agentic Workflow)")
root.geometry("620x550")
root.resizable(False, False)

frame = tk.Frame(root, padx=30, pady=20)
frame.pack(expand=True, fill="both")

# 1. URL 입력 섹션
tk.Label(frame, text="1. 채용공고 분석", font=("Malgun Gothic", 11, "bold")).pack(anchor="w", pady=(0, 5))
url_entry = tk.Entry(frame, width=72, font=("Consolas", 10))
url_entry.pack(pady=(0, 15))
url_entry.insert(0, "https://") 

# 2. 파일 업로드 섹션
tk.Label(frame, text="2. 지원자 서류 등록", font=("Malgun Gothic", 11, "bold")).pack(anchor="w", pady=(0, 10))
file_frame = tk.Frame(frame)
file_frame.pack(fill="x", pady=(0, 15))

resume_btn = tk.Button(file_frame, text="이력서 등록", command=select_resume, width=15)
resume_btn.grid(row=0, column=0, padx=(0, 10), pady=5)
resume_label = tk.Label(file_frame, text="선택된 파일 없음", fg="gray", font=("Malgun Gothic", 9))
resume_label.grid(row=0, column=1, sticky="w")

portfolio_btn = tk.Button(file_frame, text="포트폴리오 등록", command=select_portfolio, width=15)
portfolio_btn.grid(row=1, column=0, padx=(0, 10), pady=5)
portfolio_label = tk.Label(file_frame, text="선택된 파일 없음", fg="gray", font=("Malgun Gothic", 9))
portfolio_label.grid(row=1, column=1, sticky="w")

# 3. 실행 버튼 섹션
tk.Label(frame, text="3. AI 에이전트 실행", font=("Malgun Gothic", 11, "bold")).pack(anchor="w", pady=(0, 10))

button_container = tk.Frame(frame)
button_container.pack(pady=5)

analysis_button = tk.Button(
    button_container, 
    text="Step 1: 통합 분석 시작", 
    command=start_analysis_workflow,
    bg="#34495E", fg="white", font=("Malgun Gothic", 10, "bold"),
    width=25, height=2, cursor="hand2"
)
analysis_button.pack(side="left", padx=5)

writer_button = tk.Button(
    button_container, 
    text="Step 2: 자기소개서 작성 시작", 
    command=start_writing_workflow,
    bg="#2980B9", fg="white", font=("Malgun Gothic", 10, "bold"),
    width=25, height=2, cursor="hand2",
    state=tk.NORMAL # 분석 데이터가 이미 있다면 바로 실행 가능하도록 NORMAL 유지
)
writer_button.pack(side="left", padx=5)

status_label = tk.Label(frame, text="원하는 작업을 선택해주세요.", font=("Malgun Gothic", 10), fg="gray", wraplength=500)
status_label.pack(pady=20)

if __name__ == "__main__":
    root.mainloop()
