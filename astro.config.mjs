import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap'; // 1. 이 줄 추가

export default defineConfig({
  site: 'https://the-besedka-loop.vercel.app', // 2. 본인의 배포된 사이트 주소 입력 (필수!)
  integrations: [sitemap()], // 3. 이 줄 추가
});
