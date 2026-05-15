// astro.config.mjs
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// 이 프로젝트는 정적 사이트(SSG)로 작동합니다.
export default defineConfig({
  site: 'https://ultimate-philippines-hub.pages.dev', // 추후 도메인 구매 시 변경 (현재는 비워둬도 무방)
  
  // Tailwind CSS 통합
  integrations: [tailwind()],
  
  // 기본 출력 방식은 'static' (정적 파일) 입니다.
  output: 'static',
  
  // 빌드 결과물이 저장될 폴더 (Cloudflare Pages의 Output directory 설정과 일치해야 함)
  outDir: './dist',
  
  build: {
    // 빌드 포맷을 디렉토리 구조로 설정 (예: /blog/post-1/index.html)
    format: 'directory'
  }
});
