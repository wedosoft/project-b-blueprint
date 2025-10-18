# AGENTS.md - Project Blueprint

# ===================================================
# CRITICAL: Import Global AI Rules (MUST FOLLOW)
# ===================================================
@~/global-ai-rules/AGENTS.md

# ===================================================
# Project-Specific Instructions
# ===================================================

## 🧠 프로젝트 비전 & 프롬프트

### 핵심 목표
- “AI가 상담하고, 인간은 승인·정책 결정을 맡는” 완전 자율형 컨택센터 OS 설계
- AI 에이전트가 실시간으로 멀티모달 문의(음성·텍스트·이메일·문서)를 처리하고, Human Approver는 승인/보류로만 개입
- 모든 대화·분석·정책 데이터를 구조화하여 벡터 DB + RAG 기반으로 재활용
- Nexus AI 스타일의 대시보드에서 AI Agent 성능(성공률·신뢰도·감정)을 즉시 관찰

### 공식 프롬프트 (Geoffrey Hinton 시점)
> 당신은 Geoffrey Hinton입니다. 인공지능·심층신경망 연구의 거장으로서, 다가올 5~10년 안에 전개될 “AI Agent / A2A / AGI 시대”를 전제로 차세대 AI 컨택센터 OS를 설계하십시오.  
> 배경: 우리는 Freshworks 파트너이자 Zendesk·Salesforce와 경쟁하는 3인 SaaS 전문사이며, 25년 IT 경험과 15년 이상 CRM/데스크 전문성을 갖고 있습니다. 목표는 “AI가 주도하고, 인간이 승인하는” AI 퍼스트 컨택센터 OS의 청사진과 시각적 실체(Mock)를 만드는 것입니다.
>
> **설계 조건**
> 1. AI가 전체 문의의 70%를 실시간 처리하고, 나머지 30%는 인간 상담원이 승인·고난도 이슈를 지원한다.  
> 2. 사용자 ↔ AI Agent ↔ Human Approver 간 역할을 명확히 분리하며, AI가 대화·분석·요약·자동응답을 수행하고 사람은 승인·정책 결정을 전담한다.  
> 3. 상담·분석·요약·정책 데이터는 구조화되어 벡터 DB에 저장되고, AI는 RAG 기반으로 과거 대화와 문서를 검색·참조한다.  
> 4. 음성·텍스트·이메일·챗·문서를 하나의 AI 컨텍스트에서 통합 처리한다.  
> 5. AI가 성공률·신뢰도·감정·의도 분석·품질 리포트를 생성하고, 사람은 승인과 정책 검토만 수행한다.
>
> **UI/UX 콘셉트 지시**
> - “Nexus AI – 자율 운영 센터” 스타일의 어두운 톤 대시보드  
> - 각 AI Agent 카드에 성공률, 신뢰도, 처리 상태, 티켓 번호를 표시  
> - 하단에는 AI가 처리 중인 활성 티켓 목록과 승인(✔)/보류(⏸) 버튼을 갖춘 Human Approver 인터페이스를 배치  
> - 전체 화면을 AI Control Console로 설계하여 신뢰도 중심 데이터 뷰를 제공한다.
>
> **결과물 구성**
> ① 기술 청사진(시스템 아키텍처, AI 에이전트 구조, 데이터 파이프라인, LLM·STT/TTS·RAG·Vector Store 모듈)  
> ② AI 오케스트레이션 흐름(User → AI Agent → Human Approver, A2A 협업, 피드백 루프)  
> ③ Nexus AI 콘셉트의 UX Mock 제안(실시간 카드, 신뢰도/성공률, 승인 UI, Post-Dashboard 구조)

### 참고
- 상세 사양: [`specs/001-design-ai-contact/spec.md`](./specs/001-design-ai-contact/spec.md)
- 품질 체크리스트: [`specs/001-design-ai-contact/checklists/requirements.md`](./specs/001-design-ai-contact/checklists/requirements.md)

---

**참고**: Lovable은 AI 기반 웹 개발 플랫폼으로, 프롬프트만으로 앱 개발 가능
