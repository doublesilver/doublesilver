### 안녕하세요, 개발자 **이은석**입니다. 👋

[![Email](https://img.shields.io/badge/Email-korea5410@gmail.com-blue?logo=gmail&logoColor=white)](mailto:korea5410@gmail.com)
[![Portfolio](https://img.shields.io/badge/Portfolio-biz--retriever-green?logo=vercel&logoColor=white)](https://biz-retriever.vercel.app)

사용자의 불편함을 해소하기 위해 **안정적인 아키텍처를 설계**하는 것에 몰입합니다.<br/>
**Node.js와 Python** 생태계를 모두 활용하며, **AI 서비스 통합 및 인프라 구축(DevOps)** 까지 주도적으로 수행합니다.

---

### 📂 주요 프로젝트 (Featured Projects)

#### 1. [Biz-Retriever - AI 기반 입찰 분석 플랫폼](https://github.com/doublesilver/biz-retriever) 🤖
> **"G2B/온비드 자동 크롤링 + Google Gemini AI 분석 + ML 투찰가 예측 + 프로덕션 배포"**

- **Live Demo**: ✅ [https://biz-retriever.vercel.app](https://biz-retriever.vercel.app) (Frontend)
- **API Service**: ✅ [https://leeeunseok.tail32c3e2.ts.net](https://leeeunseok.tail32c3e2.ts.net) (Backend)
- **개발 기간**: 2026.01.22 ~ 01.31 (**10일**, 기획/개발/배포 완료)
- **소개**: 입찰 공고 24시간 자동 수집, AI 분석, ML 기반 낙찰가 예측, Slack 실시간 알림까지 제공하는 지능형 플랫폼
- **Tech Stack**: 
  - **Backend**: `FastAPI` `PostgreSQL` `Valkey(Redis)` `Taskiq` `Google Gemini 2.5 Flash` `Docker`
  - **Frontend**: `Vanilla JavaScript` `Payhera/Naver 디자인 시스템` `Vercel` (SPA)
  - **Infra**: `Raspberry Pi` `Tailscale Funnel` `Nginx` `Prometheus + Grafana` `Let's Encrypt SSL`
- **핵심 성과**:
  - ✅ **164 Tests (100% Pass)**, 85% Coverage
  - ✅ **프로덕션 배포** (Backend: Raspberry Pi + Tailscale, Frontend: Vercel)
  - ✅ **9,572건 공고 수집** 검증 완료
  - ✅ **PostgreSQL 최적화** (SD 카드 쓰기 80% 감소, 수명 6개월 → 2-3년)
  - ✅ **자동 백업 시스템** (매일 백업 + 검증 + Slack 알림)
  - ✅ **모니터링 스택** (Prometheus + Grafana + 11개 Alert 규칙)
  - ✅ **보안 강화** (JWT, Rate Limiting, DDoS 방어, HTTPS)
  - ✅ **UI/UX 재디자인** (Payhera/Naver/Kakao 스타일, AI 느낌 제거)
- **주요 기능**:
  - G2B API 자동 크롤링 (하루 3회 스케줄링)
  - Google Gemini AI 공고 분석 및 요약
  - 키워드 기반 스마트 필터링 (중요도 자동 채점)
  - Slack 실시간 알림 (모닝 브리핑 + 마감 임박)
  - 반응형 웹 대시보드 (Kanban, 통계, Excel Export)
  - JWT 인증 (Access Token 15분 + Refresh Token 30일)
  - 사용자별 알림 설정 및 구독 모델

#### 2. [가기싫어 (Gagisiro) - 지하철 익명 채팅](https://github.com/doublesilver/subway-board) 🚇
> **"출근길(07~09시) 가장 붐비는 시간의 사람들을 연결하는 실시간 서비스"**

- **Live Service**: [https://gagisiro.com](https://gagisiro.com)
- **소개**: 1호선~9호선별 실시간 채팅방과 운영 시간 자동 제어 시스템
- **Tech**: `React` `Node.js` `Socket.IO` `PostgreSQL` `Vercel` `Railway`
- **특징**: 출근 시간대(07~09시) 자동 활성화, 익명 채팅, 실시간 동시 접속자 표시

#### 3. [AI 기반 건물 유지보수 관리 시스템](https://github.com/doublesilver/maintenance-app) 🏢
> **"AI 분류와 비동기 큐를 도입한 스마트 건물 관리 플랫폼"**

- **소개**: 민원 내용의 AI 자동 분류 및 Celery 큐를 활용한 고성능 처리 시스템
- **Tech**: `Next.js` `FastAPI` `Llama 3 (AI)` `Celery` `Redis` `Docker` `AWS S3`
- **특징**: AI 기반 민원 분류, 비동기 작업 처리, S3 파일 업로드, 관리자 대시보드

#### 4. [AI Job Matcher](https://github.com/doublesilver/ai-job-matcher) 💼
> **"대용량 채용 데이터의 비동기 수집(Scrapy) 및 LLM 기반 직무 적합도 분석 파이프라인"**

- **소개**: Scrapy 크롤러와 Gemini API를 연동한 지능형 채용 공고 분석 REST API
- **Tech**: `Python` `FastAPI` `Scrapy` `Google Gemini API` `SQLAlchemy` `JWT`
- **특징**: 비동기 크롤링, LLM 기반 직무 분석, RESTful API, JWT 인증

#### 5. [Chatwoot Custom Guide](https://github.com/doublesilver/chatwoot-portfolio) 💬
> **[Open Source Infra Optimization] "오픈소스 CS 솔루션 Chatwoot의 Docker 기반 셀프 호스팅 가이드"**

- **소개**: 복잡한 마이크로서비스 구조의 Chatwoot를 Docker Compose로 최적화하여 배포
- **Tech**: `Docker Compose` `DevOps` `PostgreSQL` `Redis` `Sidekiq`
- **특징**: 마이크로서비스 오케스트레이션, 환경 변수 관리, 프로덕션 레디 설정

---

### 🛠️ 기술 스택 (Tech Stack)

#### Frontend
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat&logo=tailwind-css&logoColor=white)

#### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white)
![Express](https://img.shields.io/badge/Express-000000?style=flat&logo=express&logoColor=white)

#### Database & Cache
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)

#### AI & ML
![Google Gemini](https://img.shields.io/badge/Gemini-4285F4?style=flat&logo=google&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)

#### DevOps & Infra
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat&logo=nginx&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazon-aws&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat&logo=vercel&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=black)

<br/>

### 💼 핵심 역량 (Core Competencies)

**Full-Stack Development**
- FastAPI + React/Next.js 기반 풀스택 개발
- RESTful API 설계 및 구현 (Swagger/OpenAPI 문서화)
- 반응형 웹 UI/UX 설계 (Payhera/Naver 디자인 시스템 적용)

**AI/ML Integration**
- Google Gemini API 실전 활용 (RAG, 자연어 처리)
- LangChain 기반 AI 워크플로우 구현
- ML 기반 예측 모델 설계 (scikit-learn)

**Database & Performance**
- PostgreSQL 비동기 ORM (SQLAlchemy 2.0) 마스터
- Redis 캐싱 전략 설계 (70% 응답 속도 개선)
- DB 성능 튜닝 (SD 카드 쓰기 80% 감소)

**DevOps & Infrastructure**
- Docker 멀티스테이지 빌드 최적화
- CI/CD 파이프라인 구축 (GitHub Actions)
- 모니터링 스택 구축 (Prometheus + Grafana)
- HTTPS/SSL 설정 (Let's Encrypt)
- DDoS 방어 및 Rate Limiting 구현

**Testing & Quality**
- pytest 기반 TDD (100% 테스트 통과, 85% 커버리지 달성)
- 3-Layer 테스트 전략 (Unit/Integration/E2E)
- API 모킹 및 비동기 테스트 설계

**Security**
- JWT 인증 (Access/Refresh Token)
- bcrypt 비밀번호 해싱
- Rate Limiting (SlowAPI)
- CORS, Host Header Validation

---

### 📊 GitHub 통계 (Stats)

<div align="center">
  
![stats graph](https://github-readme-stats-sigma-five.vercel.app/api?username=doublesilver&show_icons=true&theme=radical&include_all_commits=true&count_private=true)

![languages graph](https://github-readme-stats-sigma-five.vercel.app/api/top-langs/?username=doublesilver&layout=compact&theme=radical&langs_count=8)

</div>

---

### 🐍 Contribution Snake

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/doublesilver/doublesilver/output/github-contribution-grid-snake-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/doublesilver/doublesilver/output/github-contribution-grid-snake.svg">
    <img alt="github contribution grid snake animation" src="https://raw.githubusercontent.com/doublesilver/doublesilver/output/github-contribution-grid-snake.svg">
  </picture>
</div>

---

### 🎯 개발 철학 (Development Philosophy)

**1. 프로덕션 퍼스트 (Production-First)**
- "작동하는 것"이 아닌 "운영 가능한 것"을 목표로 개발
- 모니터링, 백업, 보안을 기본 요소로 설계
- 실제 배포 경험 (Vercel, Railway, Raspberry Pi + Tailscale)

**2. 테스트 주도 개발 (Test-Driven Development)**
- 100% 테스트 통과를 기본 목표로 설정
- 단위/통합/E2E 3-Layer 테스트 전략
- CI/CD 파이프라인 통합 자동화

**3. 사용자 중심 설계 (User-Centric Design)**
- 실사용 가능한 UX/UI 구현 (14개 편의 기능 추가)
- 접근성 고려 (Focus Ring, 키보드 네비게이션)
- 반응형 디자인 (Mobile-First)

**4. 지속적인 개선 (Continuous Improvement)**
- 코드 리뷰 및 리팩토링 습관화
- 성능 모니터링 및 최적화
- 문서화 및 지식 공유

---

### 📚 최근 학습 (Recent Learning)

- **FastAPI 비동기 패턴 마스터** (2026.01)
  - SQLAlchemy 2.0 Async ORM
  - Taskiq 비동기 작업 스케줄링
  - Async/Await 기반 REST API 설계

- **AI/LLM 통합** (2026.01)
  - Google Gemini 2.5 Flash API 실전 활용
  - LangChain RAG 구현
  - Prompt Engineering (JSON 모드, Structured Output)

- **프로덕션 인프라** (2026.01)
  - Prometheus + Grafana 모니터링 스택
  - PostgreSQL SD 카드 최적화
  - Nginx DDoS 방어 및 Rate Limiting

- **UI/UX 디자인 시스템** (2026.01)
  - Payhera/Naver/Kakao 디자인 분석
  - CSS 변수 기반 디자인 토큰
  - 미묘한 애니메이션 및 접근성 개선

---

### 🔗 Links

- **Email**: [korea5410@gmail.com](mailto:korea5410@gmail.com)
- **GitHub**: [@doublesilver](https://github.com/doublesilver)
- **Portfolio Project**: [Biz-Retriever](https://biz-retriever.vercel.app)
- **Live API**: [Biz-Retriever API](https://leeeunseok.tail32c3e2.ts.net/docs)

---

**Last Updated**: 2026-01-31 (Biz-Retriever UI/UX 재디자인 완료)  
**Current Focus**: AI 기반 서비스 개발 및 프로덕션 배포 경험 확장  
**Open to**: Full-Stack Developer / Backend Developer / AI Engineer 포지션
