import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import openai
from dotenv import load_dotenv
import pandas as pd
import PyPDF2
import docx
import io

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "demo_key")

# Page configuration
st.set_page_config(
    page_title="TF Project Manager & Email Generator",
    page_icon="📋",
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
    
    # Save the processed content
    file_path = project_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Create metadata
    metadata = {
        "original_filename": filename,
        "template_used": template_used,
        "processed_at": datetime.now().isoformat(),
        "content": content
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_path

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

def process_with_llm(content, template):
    """Process file content using OpenAI LLM with template"""
    # Check if API key is properly configured
    if not openai.api_key or openai.api_key == "demo_key":
        return f"""[데모 모드 - 실제 OpenAI API 키가 필요합니다]

템플릿에 따른 내용 정리 예시:

1. 프로젝트 개요
   - 업로드된 파일: {content[:100]}...

2. 주요 기능
   - 파일에서 추출된 기능들이 여기에 표시됩니다

3. 기술 스택
   - 분석된 기술 스택이 표시됩니다

4. 예상 일정
   - AI가 분석한 예상 일정이 표시됩니다

5. 리스크 요소
   - 식별된 리스크들이 표시됩니다

6. 성공 지표
   - 정의된 성공 지표들이 표시됩니다

실제 사용을 위해서는 .env 파일에 OPENAI_API_KEY를 설정해주세요."""
    
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

def generate_role_based_email(project_name, role, project_data):
    """Generate role-based email using project data"""
    
    # Combine all project content
    combined_content = "\n\n".join([item["content"] for item in project_data])
    
    role_prompts = {
        "Marketer": "마케터의 관점에서 이 프로젝트의 시장성, 타겟 고객, 마케팅 전략에 대한 이메일을 작성해주세요.",
        "Designer": "디자이너의 관점에서 이 프로젝트의 UI/UX, 디자인 요구사항, 사용자 경험에 대한 이메일을 작성해주세요.",
        "Engineer": "엔지니어의 관점에서 이 프로젝트의 기술적 구현, 아키텍처, 개발 계획에 대한 이메일을 작성해주세요.",
        "Project Manager": "프로젝트 매니저의 관점에서 이 프로젝트의 일정, 리소스, 리스크 관리에 대한 이메일을 작성해주세요."
    }
    
    # Check if API key is properly configured
    if not openai.api_key or openai.api_key == "demo_key":
        role_demo_emails = {
            "Marketer": f"""
제목: [{project_name}] 마케팅 전략 및 시장 진출 계획

안녕하세요,

{project_name} 프로젝트의 마케팅 관점에서 분석 결과를 공유드립니다.

**시장 기회:**
- 타겟 시장 분석 완료
- 경쟁사 대비 차별화 포인트 확인
- 고객 페르소나 정의

**마케팅 전략:**
- 디지털 마케팅 채널 활용
- 콘텐츠 마케팅 전략 수립
- 브랜딩 및 포지셔닝 계획

실제 사용을 위해서는 .env 파일에 OPENAI_API_KEY를 설정해주세요.

감사합니다.
마케팅팀 드림
            """,
            "Designer": f"""
제목: [{project_name}] UI/UX 디자인 요구사항 및 설계 방향

안녕하세요,

{project_name} 프로젝트의 디자인 관점에서 검토 결과를 공유합니다.

**사용자 경험 분석:**
- 사용자 여정 맵핑
- 인터랙션 디자인 가이드
- 접근성 고려사항

**디자인 시스템:**
- UI 컴포넌트 라이브러리
- 브랜드 가이드라인
- 반응형 디자인 전략

실제 사용을 위해서는 .env 파일에 OPENAI_API_KEY를 설정해주세요.

감사합니다.
디자인팀 드림
            """,
            "Engineer": f"""
제목: [{project_name}] 기술 아키텍처 및 개발 계획

안녕하세요,

{project_name} 프로젝트의 기술적 검토 결과를 공유드립니다.

**기술 스택:**
- 프론트엔드: React/Vue.js
- 백엔드: Node.js/Python
- 데이터베이스: PostgreSQL/MongoDB

**개발 계획:**
- 마이크로서비스 아키텍처
- CI/CD 파이프라인 구축
- 클라우드 배포 전략

실제 사용을 위해서는 .env 파일에 OPENAI_API_KEY를 설정해주세요.

감사합니다.
개발팀 드림
            """,
            "Project Manager": f"""
제목: [{project_name}] 프로젝트 관리 계획 및 일정

안녕하세요,

{project_name} 프로젝트의 관리 관점에서 계획을 공유드립니다.

**프로젝트 일정:**
- 기획 단계: 2주
- 개발 단계: 8주
- 테스트 및 배포: 2주

**리소스 관리:**
- 팀 구성 및 역할 분담
- 예산 계획 및 관리
- 리스크 식별 및 대응 방안

실제 사용을 위해서는 .env 파일에 OPENAI_API_KEY를 설정해주세요.

감사합니다.
프로젝트 관리팀 드림
            """
        }
        return role_demo_emails.get(role, f"[데모 모드] {role}의 관점에서 생성된 이메일이 여기에 표시됩니다.")
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"당신은 {role}입니다. {role_prompts.get(role, '전문가의 관점에서 이메일을 작성해주세요.')} 이메일은 정중하고 전문적인 톤으로 작성되어야 하며, 제목과 본문을 포함해야 합니다."},
                {"role": "user", "content": f"프로젝트명: {project_name}\n\n프로젝트 정보:\n{combined_content}\n\n위 정보를 바탕으로 {role}의 관점에서 이메일을 작성해주세요."}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"이메일 생성 중 오류가 발생했습니다: {str(e)}"

# Main App
def main():
    st.title("🚀 TF Project Manager & Email Generator")
    
    # API Key warning
    if not openai.api_key or openai.api_key == "demo_key":
        st.warning("⚠️ **데모 모드로 실행 중입니다.** 실제 LLM 기능을 사용하려면 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        with st.expander("🔑 API 키 설정 방법"):
            st.code("""
# 1. .env 파일 생성
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env

# 2. OpenAI API 키 발급
# https://platform.openai.com/api-keys 에서 발급

# 3. 앱 재시작
streamlit run app.py
            """)
    
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📋 Navigation")
        tab_selection = st.radio(
            "기능 선택:",
            ["📄 파일 업로드 & 정리", "📧 역할별 이메일 생성", "📊 태그별 문서 현황"]
        )
    
    if tab_selection == "📄 파일 업로드 & 정리":
        st.header("📄 파일 업로드 & 내용 정리")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📤 파일 업로드")
            uploaded_file = st.file_uploader(
                "파일을 선택하세요",
                type=['txt', 'md', 'doc', 'docx', 'pdf'],
                help="텍스트, 마크다운, 워드, PDF 파일을 지원합니다"
            )
            
        with col2:
            st.subheader("🏷️ 태그 설정")
            
            # 기존 태그 목록 가져오기
            existing_tags = get_all_projects()
            
            # 태그 선택 (기존) 또는 새로 생성
            tag_option = st.radio(
                "태그 선택 방식:",
                ["기존 태그 사용", "새 태그 생성"],
                horizontal=True
            )
            
            if tag_option == "기존 태그 사용" and existing_tags:
                project_name = st.selectbox(
                    "기존 태그 선택",
                    existing_tags,
                    help="기존에 생성된 태그에 내용을 추가합니다"
                )
            else:
                project_name = st.text_input(
                    "새 태그명",
                    placeholder="예: AI-Healthcare, Mobile-App, Marketing-Strategy",
                    help="영문, 숫자, 하이픈만 사용 가능"
                )
            
            # 태그 설명
            st.info("💡 태그는 관련된 문서들을 그룹화하는 데 사용됩니다. 같은 태그의 모든 문서가 이메일 생성에 활용됩니다.")
            
        st.subheader("📝 정리 템플릿")
        template = st.text_area(
            "LLM이 사용할 템플릿을 입력하세요",
            value="""다음 구조로 내용을 정리해주세요:

1. 프로젝트 개요
2. 주요 기능
3. 기술 스택
4. 예상 일정
5. 리스크 요소
6. 성공 지표""",
            height=200
        )
        
        if st.button("🔄 내용 정리 및 저장", type="primary", width="stretch"):
            if uploaded_file and project_name and template:
                with st.spinner("파일을 처리중입니다..."):
                    # Read file content using the new function
                    content = read_file_content(uploaded_file)
                    
                    # Process with LLM
                    processed_content = process_with_llm(content, template)
                    
                    # Save to project folder
                    saved_path = save_project_file(
                        project_name, 
                        uploaded_file.name, 
                        processed_content, 
                        template
                    )
                    
                    st.success(f"✅ 파일이 성공적으로 처리되어 '{project_name}' 태그에 저장되었습니다!")
                    st.info(f"🏷️ 태그: {project_name} | 📂 저장 위치: {saved_path}")
                    
                    # Show processed content
                    with st.expander("📋 처리된 내용 미리보기"):
                        st.markdown(processed_content)
            else:
                st.error("모든 필드를 입력해주세요.")
    
    elif tab_selection == "📧 역할별 이메일 생성":
        st.header("📧 역할별 맞춤 이메일 생성")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🏷️ 태그 선택")
            tags = get_all_projects()
            
            if not tags:
                st.warning("저장된 태그가 없습니다. 먼저 파일을 업로드해주세요.")
            else:
                selected_project = st.selectbox(
                    "태그 선택",
                    tags,
                    help="생성된 태그 목록에서 선택하세요"
                )
                
                if selected_project:
                    project_files = get_project_files(selected_project)
                    st.info(f"📁 {len(project_files)}개의 문서가 이 태그에 저장되어 있습니다")
                    
                    # 태그별 요약 정보 표시
                    with st.expander(f"📋 '{selected_project}' 태그 요약"):
                        if project_files:
                            latest_files = sorted(project_files, key=lambda x: x.get('processed_at', ''), reverse=True)[:3]
                            st.write("**최근 문서 3개:**")
                            for i, file_info in enumerate(latest_files, 1):
                                st.write(f"{i}. {file_info.get('original_filename', 'Unknown')} - {file_info.get('processed_at', 'Unknown')[:10]}")
                        
                        # 태그 통계
                        total_docs = len(project_files)
                        st.metric("총 문서 수", total_docs)
        
        with col2:
            st.subheader("👤 역할 선택")
            role = st.selectbox(
                "이메일을 작성할 역할을 선택하세요",
                ["Marketer", "Designer", "Engineer", "Project Manager"],
                help="선택한 역할의 관점에서 이메일이 생성됩니다"
            )
            
            # Role description
            role_descriptions = {
                "Marketer": "🎯 시장성, 고객, 마케팅 전략 중심",
                "Designer": "🎨 UI/UX, 디자인, 사용자 경험 중심", 
                "Engineer": "⚙️ 기술 구현, 아키텍처, 개발 중심",
                "Project Manager": "📊 일정, 리소스, 리스크 관리 중심"
            }
            
            st.info(role_descriptions.get(role, ""))
        
        if st.button("📧 이메일 생성", type="primary", width="stretch"):
            if tags and 'selected_project' in locals() and selected_project:
                project_files = get_project_files(selected_project)
                
                if project_files:
                    with st.spinner(f"{role} 관점에서 '{selected_project}' 태그 기반 이메일을 생성중입니다..."):
                        email_content = generate_role_based_email(
                            selected_project, 
                            role, 
                            project_files
                        )
                        
                        st.success("✅ 이메일이 성공적으로 생성되었습니다!")
                        
                        # Display email
                        st.subheader(f"📧 {role}의 '{selected_project}' 태그 기반 이메일")
                        st.markdown("---")
                        st.markdown(email_content)
                        
                        # Copy to clipboard button
                        st.code(email_content, language="markdown")
                else:
                    st.error("선택한 태그에 문서가 없습니다.")
            else:
                st.error("태그를 선택해주세요.")
    
    else:  # 태그 현황
        st.header("📊 태그별 문서 현황")
        
        tags = get_all_projects()
        
        if not tags:
            st.info("🏷️ 아직 생성된 태그가 없습니다.")
            st.markdown("파일 업로드 탭에서 첫 번째 태그를 만들어보세요!")
        else:
            st.subheader(f"🏷️ 총 {len(tags)}개의 태그")
            
            # 태그별 통계 요약
            total_docs = 0
            tag_stats = []
            for tag in tags:
                files = get_project_files(tag)
                doc_count = len(files)
                total_docs += doc_count
                latest_date = max([f.get('processed_at', '2000-01-01') for f in files]) if files else '없음'
                tag_stats.append({
                    "태그": tag,
                    "문서 수": doc_count,
                    "최근 업데이트": latest_date[:10] if latest_date != '없음' else '없음'
                })
            
            # 전체 통계
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전체 태그 수", len(tags))
            with col2:
                st.metric("전체 문서 수", total_docs)
            with col3:
                avg_docs = total_docs / len(tags) if tags else 0
                st.metric("태그당 평균 문서", f"{avg_docs:.1f}개")
            
            # 태그별 상세 정보
            st.subheader("📋 태그별 상세 현황")
            for tag in tags:
                with st.expander(f"🏷️ {tag}"):
                    files = get_project_files(tag)
                    
                    if files:
                        st.write(f"📄 문서 수: {len(files)}개")
                        
                        # Create a simple table
                        file_data = []
                        for file_info in files:
                            file_data.append({
                                "파일명": file_info.get("original_filename", "Unknown"),
                                "처리일시": file_info.get("processed_at", "Unknown")[:19].replace("T", " "),
                                "템플릿 사용": "✅" if file_info.get("template_used") else "❌"
                            })
                        
                        if file_data:
                            df = pd.DataFrame(file_data)
                            st.dataframe(df, width="stretch")
                            
                            # 태그 요약 미리보기
                            latest_content = files[0].get('content', '')[:200]
                            if latest_content:
                                st.write("**최근 문서 내용 미리보기:**")
                                st.text(latest_content + "..." if len(latest_content) >= 200 else latest_content)
                    else:
                        st.warning("문서가 없습니다.")

    # Footer
    st.markdown("---")
    st.markdown("🏗️ **TF Project Manager** | Made with ❤️ using Streamlit")

if __name__ == "__main__":
    main()
