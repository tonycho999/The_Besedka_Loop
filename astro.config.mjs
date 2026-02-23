import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  // 👇 이 부분이 없어서 에러가 난 것입니다!
  site: 'https://the-besedka-loop.vercel.app', 
  
  // 👇 사이트맵 플러그인 추가
  integrations: [sitemap()],
});
