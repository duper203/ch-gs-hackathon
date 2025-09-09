import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import openai
import requests
from dotenv import load_dotenv
import pandas as pd
import PyPDF2
import docx
import io

# Import templates from separate file
from templates import (
    DEMO_CONTENT_TEMPLATE,
    DEMO_EMAIL_TEMPLATE, 
    SYSTEM_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE,
    get_predefined_templates
)

# Load environment variables
load_dotenv()

# Configure APIs
openai.api_key = os.getenv("OPENAI_API_KEY", "demo_key")
MISO_API_KEY = os.getenv("MISO_API_KEY", "")
MISO_DATASET_ID = os.getenv("MISO_DATASET_ID", "")
MISO_BASE_URL = "https://api.holdings.miso.gs/ext/v1"

# Channel.io API configuration
CHANNEL_API_URL = os.getenv("CHANNEL_API_URL", "")
CHANNEL_ACCESS_KEY = os.getenv("CHANNEL_ACCESS_KEY", "")
CHANNEL_ACCESS_SECRET = os.getenv("CHANNEL_ACCESS_SECRET", "")

# Page configuration
st.set_page_config(
    page_title="TF Project Manager & Email Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create data directory if it doesn't exist
DATA_DIR = Path("tf_projects")
DATA_DIR.mkdir(exist_ok=True)



def save_project_file(project_name, filename, content, template_used):
    """Save processed file content to project folder"""
    project_dir = DATA_DIR / project_name
    project_dir.mkdir(exist_ok=True)
    
    # Generate file number based on existing files
    existing_files = list(project_dir.glob("*.txt"))
    sync_number = len(existing_files) + 1
    
    # Save with convention: 날짜_sync_번호
    today = datetime.now().strftime('%Y%m%d')
    generated_filename = f"{today}_sync_{sync_number}"
    file_path = project_dir / f"{generated_filename}.txt"
    
    # Create metadata
    metadata = {
        "original_filename": filename,
        "template_used": template_used,
        "processed_at": datetime.now().isoformat(),
        "content": content,
        "sync_number": sync_number,
        "date": today,
        "generated_filename": generated_filename
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_path, generated_filename


def get_project_files(project_name):
    """Get all files for a specific project"""
    project_dir = DATA_DIR / project_name
    if not project_dir.exists():
        return []
    
    files = []
    for file_path in project_dir.glob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                files.append(metadata)
        except:
            continue
    
    return files

def get_all_projects():
    """Get list of all projects"""
    if not DATA_DIR.exists():
        return []
    return [d.name for d in DATA_DIR.iterdir() if d.is_dir()]


def delete_project_file(project_name, file_index):
    """Delete a specific file from project"""
    project_dir = DATA_DIR / project_name
    if not project_dir.exists():
        return False
    
    files = list(project_dir.glob("*.txt"))
    if 0 <= file_index < len(files):
        files[file_index].unlink()
        return True
    return False


def delete_entire_project(project_name):
    """Delete entire project and all its files"""
    project_dir = DATA_DIR / project_name
    if not project_dir.exists():
        return False
    
    # Delete all files in the project
    for file_path in project_dir.glob("*.txt"):
        file_path.unlink()
    
    # Delete the project directory
    project_dir.rmdir()
    return True


def read_file_content(uploaded_file):
    """Read content from uploaded file based on file type"""
    try:
        file_type = uploaded_file.type
        file_name = uploaded_file.name.lower()
        
        if file_type.startswith('text/') or file_name.endswith('.txt') or file_name.endswith('.md'):
            # Text files
            content = str(uploaded_file.read(), "utf-8")
            
        elif file_name.endswith('.pdf'):
            # PDF files
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
                
        elif file_name.endswith('.docx'):
            # Word documents
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        else:
            # Try to read as text file
            try:
                content = str(uploaded_file.read(), "utf-8")
            except UnicodeDecodeError:
                content = f"파일 형식을 지원하지 않습니다: {file_name}\n지원 형식: .txt, .md, .pdf, .docx"
        
        return content
        
    except Exception as e:
        return f"파일 읽기 중 오류가 발생했습니다: {str(e)}"


def upload_to_miso_api(document_name, processed_text):
    """Upload processed text to MISO API as a document"""
    if not MISO_API_KEY or not MISO_DATASET_ID:
        return {
            "success": False,
            "message": "MISO API 키 또는 데이터셋 ID가 설정되지 않았습니다.",
            "demo": True
        }
    
    try:
        # API 연결 테스트 먼저 수행
        test_url = f"{MISO_BASE_URL}"
        test_response = requests.get(test_url, timeout=10)
        
        if test_response.status_code != 200:
            return {
                "success": False,
                "message": f"MISO API 서버 연결 실패: {test_response.status_code}",
                "demo": False
            }
        
        # 실제 문서 업로드 요청
        url = f"{MISO_BASE_URL}/datasets/{MISO_DATASET_ID}/docs/text"
        
        headers = {
            "Authorization": f"Bearer {MISO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": document_name,
            "text": processed_text,
            "indexing_type": "high_quality",
            "process_rule": {
                "mode": "automatic"
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": "MISO API에 성공적으로 업로드되었습니다!",
                "document_id": result.get("document", {}).get("id", ""),
                "batch": result.get("batch", ""),
                "demo": False
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": f"MISO API 엔드포인트를 찾을 수 없습니다. 데이터셋 ID({MISO_DATASET_ID})를 확인해주세요.",
                "demo": False,
                "debug_info": f"URL: {url}"
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "message": "MISO API 인증 실패. API 키를 확인해주세요.",
                "demo": False
            }
        else:
            return {
                "success": False,
                "message": f"MISO API 오류: {response.status_code} - {response.text[:200]}",
                "demo": False,
                "debug_info": f"URL: {url}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "MISO API 요청 시간 초과. 네트워크 연결을 확인해주세요.",
            "demo": False
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "MISO API 서버에 연결할 수 없습니다. 네트워크 또는 URL을 확인해주세요.",
            "demo": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"MISO API 호출 중 예상치 못한 오류 발생: {str(e)}",
            "demo": False
        }


def send_to_channel(email_content, person_name, project_name):
    """Send email content to Channel.io group"""
    try:
        headers = {
            "accept": "application/json",
            "x-access-key": CHANNEL_ACCESS_KEY,
            "x-access-secret": CHANNEL_ACCESS_SECRET,
            "Content-Type": "application/json"
        }
        
        # Create message for Channel.io
        message_text = f"{person_name}님을 위한 {project_name} TF 프로젝트 맞춤 요약이 생성되었습니다.\n\n{email_content}"
        
        payload = {
            "blocks": [
                {
                    "type": "text",
                    "value": message_text
                }
            ]
        }
        
        response = requests.post(CHANNEL_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200 or response.status_code == 201:
            return {
                "success": True,
                "message": "채널 방에 성공적으로 전송되었습니다!"
            }
        else:
            return {
                "success": False,
                "message": f"채널 전송 실패: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"채널 전송 중 오류 발생: {str(e)}"
        }


def process_with_llm(content, template):
    """Process file content using OpenAI LLM with template"""
    # Check if API key is properly configured
    if not openai.api_key or openai.api_key == "demo_key":
        return DEMO_CONTENT_TEMPLATE.format(content_preview=content[:100])
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"다음 템플릿을 사용하여 제공된 내용을 정리하고 구조화해주세요:\n\n{template}"},
                {"role": "user", "content": f"다음 내용을 위의 템플릿에 맞춰 정리해주세요:\n\n{content}"}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM 처리 중 오류가 발생했습니다: {str(e)}"


def generate_role_based_email(project_name, context_info, project_data):
    """Generate role-based email using project data and 3-category context information"""
    
    # Combine all project content
    combined_content = "\n\n".join([item["content"] for item in project_data])
    
    # Check if API key is properly configured
    if not openai.api_key or openai.api_key == "demo_key":
        return DEMO_EMAIL_TEMPLATE.format(
            meeting_subject=context_info['meeting_subject'],
            organization=context_info['organization'],
            person_name=context_info['person_name'],
            org_role_description=context_info['org_role_description'],
            person_role=context_info['person_role'],
            project_name=project_name
        )
    
    try:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            person_name=context_info['person_name'],
            organization=context_info['organization'],
            meeting_subject=context_info['meeting_subject'],
            org_role_description=context_info['org_role_description'],
            person_role=context_info['person_role']
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            project_name=project_name,
            meeting_subject=context_info['meeting_subject'],
            combined_content=combined_content,
            organization=context_info['organization'],
            person_name=context_info['person_name']
        )
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"이메일 생성 중 오류가 발생했습니다: {str(e)}"


# Main App
def main():
    st.title("TF Project Manager & Email Generator")
    
    # API Key warning for OpenAI only
    if not openai.api_key or openai.api_key == "demo_key":
        st.warning("**데모 모드로 실행 중입니다.** 실제 LLM 기능을 사용하려면 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
    
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        tab_selection = st.radio(
            "기능 선택:",
            ["오프라인 미팅 기록 업로드", "담당자별 맞춤 요약", "TF명별 문서 현황"],
            index=0  # 첫 번째 탭을 기본값으로 설정
        )
    
    if tab_selection == "오프라인 미팅 기록 업로드":
        st.header("오프라인 미팅 STT 기록 업로드")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("미팅 기록 업로드")
            uploaded_file = st.file_uploader(
                "미팅 STT 기록 파일을 선택하세요",
                type=['txt', 'md', 'doc', 'docx', 'pdf'],
                help="텍스트, 마크다운, 워드, PDF 파일을 지원합니다"
            )
            
        with col2:
            st.subheader("TF 프로젝트명")
            
            # 기존 태그 목록 가져오기
            existing_tags = get_all_projects()
            
            # 프로젝트 선택 (기존) 또는 새로 생성
            tag_option = st.radio(
                "프로젝트 선택 방식:",
                ["기존 프로젝트 사용", "새 프로젝트 생성"],
                horizontal=True
            )
            
            if tag_option == "기존 프로젝트 사용" and existing_tags:
                project_name = st.selectbox(
                    "기존 프로젝트 선택",
                    existing_tags,
                    help="기존에 생성된 프로젝트에 미팅 기록을 추가합니다"
                )
            else:
                project_name = st.text_input(
                    "새 프로젝트명",
                    placeholder="예: AI-Healthcare, Mobile-App, Marketing-Strategy",
                    help="영문, 숫자, 하이픈만 사용 가능"
                )
            
            # 프로젝트 설명
            st.info("TF 프로젝트명은 관련된 미팅 기록들을 그룹화하는 데 사용됩니다. 같은 프로젝트의 모든 미팅 기록이 이메일 생성에 활용됩니다.")
            
        st.subheader("정리 템플릿")
        
        # 템플릿 선택
        predefined_templates = get_predefined_templates()
        
        selected_template_name = st.selectbox(
            "기본 템플릿 선택:",
            list(predefined_templates.keys()),
            help="용도에 맞는 기본 템플릿을 선택하세요"
        )
        
        # 선택된 템플릿 미리보기
        with st.expander("선택된 템플릿 미리보기"):
            st.markdown(predefined_templates[selected_template_name])
        
        # 커스터마이징 옵션
        customize_option = st.radio(
            "템플릿 사용 방식:",
            ["기본 템플릿 그대로 사용", "추가 프롬프트로 커스터마이징"],
            horizontal=True,
            help="기본 템플릿을 그대로 사용하거나, 추가 요청사항을 더해서 커스터마이징할 수 있습니다"
        )
        
        base_template = predefined_templates[selected_template_name]
        
        if customize_option == "추가 프롬프트로 커스터마이징":
            st.write(f"**'{selected_template_name}' 템플릿에 추가 요청사항:**")
            additional_prompt = st.text_area(
                "추가로 반영하고 싶은 내용을 작성하세요",
                value="",
                height=150,
                placeholder="""예시:
- 더 구체적인 수치와 데이터 포함해서 정리
- 경쟁사 분석 부분을 더 자세히 작성
- 실행 가능한 액션 플랜 중심으로 정리
- 리스크 요소를 더 세밀하게 분석""",
                help="선택한 기본 템플릿에 추가로 반영하고 싶은 요청사항을 자유롭게 작성하세요"
            )
            
            if additional_prompt.strip():
                template = f"""{base_template}

--- 추가 요청사항 ---
{additional_prompt.strip()}

위의 기본 템플릿 구조를 따르되, 추가 요청사항을 반영하여 더욱 상세하고 맞춤화된 내용으로 정리해주세요."""
            else:
                template = base_template
        else:
            template = base_template
        
        # MISO API 업로드 옵션
        if MISO_API_KEY and MISO_DATASET_ID:
            upload_to_miso = st.checkbox(
                "MISO 지식에도 업로드하기", 
                value=False,
                help="처리된 미팅 기록을 MISO 지식베이스에도 저장합니다"
            )
        else:
            upload_to_miso = False
        
        if st.button("미팅 기록 정리 및 저장", type="primary", width="stretch"):
            if uploaded_file and project_name and template:
                with st.spinner("미팅 기록을 처리중입니다..."):
                    # Read file content using the new function
                    content = read_file_content(uploaded_file)
                    
                    # Process with LLM
                    processed_content = process_with_llm(content, template)
                    
                    # Save to project folder
                    saved_path, generated_filename = save_project_file(
                        project_name, 
                        uploaded_file.name, 
                        processed_content, 
                        template
                    )
                    
                    # Show success message for local save
                    st.success(f"✅ '{project_name}' 프로젝트에 저장 완료")
                    
                    # MISO API 업로드 (조용히 실행)
                    if upload_to_miso:
                        miso_result = upload_to_miso_api(generated_filename, processed_content)
                    
                    # Show processed content
                    with st.expander("정리된 미팅 기록 미리보기"):
                        st.markdown(processed_content)
            else:
                st.error("모든 필드를 입력해주세요.")
    
    elif tab_selection == "담당자별 맞춤 요약":
        st.header("담당자별 맞춤 미팅 요약 이메일")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("TF명 선택")
            tags = get_all_projects()
            
            if not tags:
                st.warning("저장된 TF 프로젝트가 없습니다. 먼저 파일을 업로드해주세요.")
            else:
                selected_project = st.selectbox(
                    "TF 프로젝트 선택",
                    tags,
                    help="생성된 TF 프로젝트 목록에서 선택하세요"
                )
                
                if selected_project:
                    project_files = get_project_files(selected_project)
                    st.info(f"{len(project_files)}개의 문서가 이 TF 프로젝트에 저장되어 있습니다")
                    
                    # TF명별 요약 정보 표시
                    with st.expander(f"'{selected_project}' TF 프로젝트 요약"):
                        if project_files:
                            latest_files = sorted(project_files, key=lambda x: x.get('processed_at', ''), reverse=True)[:3]
                            st.write("**최근 문서 3개:**")
                            for i, file_info in enumerate(latest_files, 1):
                                st.write(f"{i}. {file_info.get('original_filename', 'Unknown')} - {file_info.get('processed_at', 'Unknown')[:10]}")
                        
                        # 태그 통계
                        total_docs = len(project_files)
                        st.metric("총 문서 수", total_docs)
        
                        with col2:
                            st.subheader("받는 사람 정보")
                            
                            # 1. 주제 (미팅이 소속된 프로젝트명)
                            st.write("**1. 주제 (미팅 소속 프로젝트명)**")
                            meeting_subject = st.text_input(
                                "이 미팅이 소속된 프로젝트명을 입력하세요",
                                placeholder="예: GS PLAI HACKATHON 기획 TF팀",
                                help="미팅이 어떤 프로젝트나 TF팀 소속인지 입력하세요"
                            )
                            
                            # 2. 조직 (받는 사람의 소속 조직)
                            st.write("**2. 조직 (받는 사람의 소속 조직)**")
                            organization_option = st.radio(
                                "조직 입력 방식:",
                                ["기본 조직 선택", "새 조직 입력"],
                                horizontal=True
                            )
                            
                            default_orgs = ["사업개발", "제품팀", "마케팅", "기획", "개발", "디자인", "경영지원"]
                            
                            if organization_option == "기본 조직 선택":
                                organization = st.selectbox(
                                    "소속 조직 선택",
                                    default_orgs,
                                    help="담당자가 소속된 정규 조직을 선택하세요"
                                )
                            else:
                                organization = st.text_input(
                                    "새 조직명",
                                    placeholder="예: 특별기획팀, 신사업TF",
                                    help="TF팀이나 새로운 조직명을 입력하세요"
                                )
                            
                            # 조직 역할 설명
                            org_role_description = st.text_area(
                                "조직의 역할과 책임을 설명해주세요",
                                value="",
                                placeholder="""예시: 채널코퍼레이션의 사업적 성공을 위한 대외 관계를 개척/관리하고 대내 기능 간 커뮤니케이터 수행

1. 규격화되지 않고, 복잡하나 중요한 문제가 있으면 먼저 부딪혀보고 '일이 되게 만듦'(Getting Things Done)
2. 대외) 파트너와의 관계를 다지는 tech-revenue 파트너십부터 고객사 미팅, IR 등에도 부분적 투입됨
3. 대내) 주로 비즈 - 제품 팀간 가교 역할을 수행함""",
                                height=100,
                                help="이 조직의 핵심 역할과 책임을 설명해주세요"
                            )
                            
                            # 3. 받는 사람 (이름과 역할 설명)
                            st.write("**3. 받는 사람 (이름과 역할 설명)**")
                            person_name = st.text_input(
                                "받는 사람 이름",
                                placeholder="예: 문희철(henry)",
                                help="미팅 요약을 받을 담당자의 이름을 입력하세요"
                            )
                            
                            person_role = st.text_area(
                                "받는 사람의 구체적인 역할을 설명해주세요",
                                placeholder="예: 헨리는 사업개발 팀의 매니저입니다. CEO인 레드가 직속 보고라인입니다. 여러 조직(사업개발, 신사업TF)에 소속되어 있습니다.",
                                height=80,
                                help="받는 사람의 직책, 보고라인, 주요 업무, 복수 조직 소속 여부 등을 설명해주세요"
                            )
        
        # Channel.io 전송 옵션
        st.subheader("📱 채널 방 자동 전송")
        send_to_channel_option = st.checkbox(
            "생성된 요약을 채널 방에 자동 전송하기",
            value=True,
            help="이메일 생성 후 자동으로 채널 방에 메시지를 전송합니다"
        )
        
        if st.button("맞춤 요약 이메일 생성", type="primary", width="stretch"):
            # 필수 필드 검증
            missing_fields = []
            if not tags or not 'selected_project' in locals() or not selected_project:
                missing_fields.append("TF 프로젝트")
            if not meeting_subject:
                missing_fields.append("주제 (미팅 소속 프로젝트명)")
            if not organization:
                missing_fields.append("조직")
            if not person_name:
                missing_fields.append("받는 사람 이름")
            
            if missing_fields:
                st.error(f"다음 필드를 입력해주세요: {', '.join(missing_fields)}")
            else:
                project_files = get_project_files(selected_project)
                
                if project_files:
                    # 3개 카테고리 정보 구성
                    context_info = {
                        # 1. 주제 (미팅이 소속된 프로젝트명)
                        "meeting_subject": meeting_subject,
                        # 2. 조직 (담당자의 소속 조직)
                        "organization": organization,
                        "org_role_description": org_role_description,
                        # 3. 담당자 (이름과 역할 설명)
                        "person_name": person_name,
                        "person_role": person_role
                    }
                    
                    with st.spinner(f"{person_name}({organization})님을 위한 '{selected_project}' TF 프로젝트 맞춤 요약을 생성중입니다..."):
                        email_content = generate_role_based_email(
                            selected_project, 
                            context_info, 
                            project_files
                        )
                        
                        st.success("맞춤 요약 이메일이 성공적으로 생성되었습니다!")
                        
                        # Send to Channel.io if option is enabled
                        if send_to_channel_option:
                            with st.spinner("채널 방에 전송 중..."):
                                channel_result = send_to_channel(email_content, person_name, selected_project)
                                if channel_result["success"]:
                                    st.success(f"📱 {channel_result['message']}")
                                else:
                                    st.warning(f"⚠️ {channel_result['message']}")
                        
                        # Display email
                        st.subheader(f"{person_name}({organization})님을 위한 '{selected_project}' TF 프로젝트 맞춤 요약")
                        st.markdown("---")
                        st.markdown(email_content)
                        
                        # Copy to clipboard section
                        st.markdown("---")
                        st.write("**📋 복사용 텍스트:**")
                        with st.expander("클릭하여 복사용 텍스트 보기"):
                            st.text_area(
                                "이메일 내용 (복사용)",
                                value=email_content,
                                height=300,
                                help="이 텍스트를 복사해서 이메일로 사용하세요"
                            )
                else:
                    st.error("선택한 TF 프로젝트에 문서가 없습니다.")
    
    else:  # TF명 현황
        st.header("TF명별 문서 현황")
        
        tags = get_all_projects()
        
        if not tags:
            st.info("아직 생성된 TF 프로젝트가 없습니다.")
            st.markdown("파일 업로드 탭에서 첫 번째 TF 프로젝트를 만들어보세요!")
        else:
            # Header with reset button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"총 {len(tags)}개의 TF 프로젝트")
            with col2:
                if st.button("전체 초기화", type="secondary", help="모든 프로젝트와 파일을 삭제합니다"):
                    # Delete all projects
                    for tag in tags:
                        delete_entire_project(tag)
                    st.success("모든 데이터가 초기화되었습니다!")
                    st.rerun()
            
            # TF명별 통계 요약
            total_docs = 0
            project_stats = []
            for project in tags:
                files = get_project_files(project)
                doc_count = len(files)
                total_docs += doc_count
                latest_date = max([f.get('processed_at', '2000-01-01') for f in files]) if files else '없음'
                project_stats.append({
                    "TF 프로젝트": project,
                    "문서 수": doc_count,
                    "최근 업데이트": latest_date[:10] if latest_date != '없음' else '없음'
                })
            
            # 전체 통계
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전체 TF 프로젝트 수", len(tags))
            with col2:
                st.metric("전체 문서 수", total_docs)
            with col3:
                avg_docs = total_docs / len(tags) if tags else 0
                st.metric("프로젝트당 평균 문서", f"{avg_docs:.1f}개")
            
            # TF명별 상세 정보 - 표 형식으로 복원
            st.subheader("TF명별 상세 현황")
            
            # 전체 삭제 버튼을 위한 공간
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("전체 데이터 삭제", type="secondary", help="모든 프로젝트와 파일을 삭제합니다"):
                    for tag in tags:
                        delete_entire_project(tag)
                    st.success("모든 데이터가 삭제되었습니다!")
                    st.rerun()
            
            for project in tags:
                with st.expander(f"TF 프로젝트: {project}"):
                    files = get_project_files(project)
                    
                    if files:
                        st.write(f"**문서 수**: {len(files)}개")
                        
                        # 표 형식으로 파일 목록 표시
                        file_data = []
                        for i, file_info in enumerate(files):
                            sync_info = f"sync_{file_info.get('sync_number', 'N/A')}" if file_info.get('sync_number') else "Legacy"
                            date_info = file_info.get('date', file_info.get('processed_at', 'Unknown')[:10])
                            file_data.append({
                                "파일명": f"{date_info}_{sync_info}",
                                "원본 파일명": file_info.get("original_filename", "Unknown"),
                                "처리일시": file_info.get("processed_at", "Unknown")[:19].replace("T", " "),
                                "템플릿 사용": "사용함" if file_info.get("template_used") else "미사용",
                                "삭제": f"delete_file_{project}_{i}"
                            })
                        
                        if file_data:
                            # 삭제 버튼들을 위한 행
                            for i, row in enumerate(file_data):
                                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                                with col1:
                                    st.write(row["파일명"])
                                with col2:
                                    st.write(row["원본 파일명"])
                                with col3:
                                    st.write(row["처리일시"])
                                with col4:
                                    st.write(row["템플릿 사용"])
                                with col5:
                                    if st.button("삭제", key=f"delete_file_{project}_{i}", type="secondary"):
                                        if delete_project_file(project, i):
                                            st.success("파일이 삭제되었습니다!")
                                            st.rerun()
                                        else:
                                            st.error("삭제 실패!")
                            
                            # 프로젝트 전체 삭제 버튼
                            st.markdown("---")
                            if st.button(f"'{project}' 프로젝트 전체 삭제", key=f"delete_project_{project}", type="secondary"):
                                if delete_entire_project(project):
                                    st.success(f"'{project}' 프로젝트가 삭제되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("프로젝트 삭제 실패!")
                        
                    else:
                        st.warning("문서가 없습니다.")

    # Footer
    st.markdown("---")
    st.markdown("**TF Project Manager** | Made with Streamlit")


if __name__ == "__main__":
    main()
