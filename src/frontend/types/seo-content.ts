/**
 * S5: src/pipeline/schemas/seo_content_schema.json 변경 시 반드시 이 파일도 동시 업데이트.
 * JSON 스키마와 이 TypeScript 인터페이스는 항상 동기화 상태를 유지해야 합니다.
 */

export interface SeoContentJson {
  /** 시설 소개 문단 (50자 이상) */
  intro: string;

  /** 시설 주요 특장점 목록 (3~6개) */
  highlights: string[];

  /** 제공 서비스 안내 문단 (50자 이상) */
  care_services: string;

  /** 위치 및 교통 안내 문단 (30자 이상) */
  location_info: string;

  /** 시설 현황 및 규모 안내 문단 (30자 이상) */
  facility_info: string;

  /** 종합 요약 문단 (50자 이상) */
  summary: string;
}
